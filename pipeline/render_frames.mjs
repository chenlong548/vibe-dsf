#!/usr/bin/env node
/* =====================================================================
 * render_frames.mjs —— 把 index.html 逐帧"拍"成 PNG 序列
 *
 * 两种模式：
 *   --fast   （默认）CDP 长连接：一个 Chrome 进程复用 N 个会话并行截图。
 *            省掉每帧 500ms 的进程启动开销，实测比 legacy 快 3–8 倍。
 *   --slow   旧行为：每帧起一个独立 Chrome 进程（--screenshot 参数法）。
 *            fast 模式启动失败时也会自动回退到这里，保证总能出帧。
 *
 * 用法（在你的项目目录里跑，输出落在当前目录）：
 *   node ../pipeline/render_frames.mjs                      # 全片，默认 30fps / 26s
 *   node ../pipeline/render_frames.mjs --duration 120       # 2 分钟片
 *   node ../pipeline/render_frames.mjs --start 12 --end 16  # 只重渲 12~16 秒
 *   node ../pipeline/render_frames.mjs --stills 2,6,13,18   # 只出几张静帧（定风格用）
 *   node ../pipeline/render_frames.mjs --slow               # 强制旧模式
 * ===================================================================== */

import { spawn } from 'node:child_process';
import { mkdirSync, existsSync, statSync, rmSync, writeFileSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import os from 'node:os';

const __dirname = dirname(fileURLToPath(import.meta.url));

/* ---------- 参数 ---------- */
function arg(name, def){
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] && !process.argv[i + 1].startsWith('--')
    ? process.argv[i + 1] : def;
}
function hasFlag(name){ return process.argv.includes(`--${name}`); }

const HTML     = resolve(arg('html', 'index.html'));
const OUT      = resolve(arg('out', 'frames'));
const FPS      = parseFloat(arg('fps', '30'));
const DURATION = parseFloat(arg('duration', '26'));
const START    = parseFloat(arg('start', '0'));
const WIDTH    = parseInt(arg('width', '1920'), 10);
const HEIGHT   = parseInt(arg('height', '1080'), 10);
const CONC     = parseInt(arg('concurrency', '4'), 10);
const BUDGET   = arg('budget', '4000');   // legacy 模式：页面稳定后等多少虚拟毫秒再截图
const STILLS   = arg('stills', null);
const USE_FAST = !hasFlag('slow');        // 默认 fast，--slow 回到旧行为

/* ---------- 找 Chrome ---------- */
const CANDIDATES = [
  process.env.CHROME_PATH,
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  join(os.homedir(), 'AppData\\Local\\Google\\Chrome\\Application\\chrome.exe'),
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser'
].filter(Boolean);

const CHROME = CANDIDATES.find(p => { try { return existsSync(p) && statSync(p).isFile(); } catch { return false; } });
if (!CHROME){
  console.error('✗ 找不到 Chrome。请设置环境变量 CHROME_PATH 指向 chrome.exe');
  process.exit(1);
}

const URL_BASE = pathToFileURL(HTML).href;

/* ---------- 任务清单 ---------- */
mkdirSync(OUT, { recursive: true });

let jobs = [];
let mode = '全片';
if (STILLS){
  jobs = STILLS.split(',').map(s => parseFloat(s.trim())).filter(n => !Number.isNaN(n))
    .map(t => ({ t, file: join(OUT, `still_${t.toFixed(2)}.png`) }));
  mode = `静帧 ${jobs.length} 张`;
} else {
  const END = arg('end', null);
  const endT = END ? parseFloat(END) : DURATION;
  const first = Math.round(START * FPS);
  const last  = Math.round(endT * FPS);
  for (let i = first; i < last; i++){
    const t = i / FPS;
    if (t > DURATION) break;
    jobs.push({ t, file: join(OUT, `frame_${String(i + 1).padStart(5, '0')}.png`) });
  }
  if (!jobs.length){
    console.error(`✗ 区间为空：start=${START}s end=${endT}s。--duration 是全片总长，只重渲一段请用 --start/--end`);
    process.exit(1);
  }
}
console.log(`[${mode}] 共 ${jobs.length} 帧  ${WIDTH}x${HEIGHT} @ ${FPS}fps`);
console.log(`HTML: ${HTML}`);
console.log(`Chrome: ${CHROME}`);

/* ---------- 进度 ---------- */
const t0 = Date.now();
let done = 0, failed = 0;
function progress(){
  const el = (Date.now() - t0) / 1000;
  const eta = done ? (el / done) * (jobs.length - done) : 0;
  process.stdout.write(`\r  ${done}/${jobs.length} 帧   ${el.toFixed(1)}s   预计剩余 ${eta.toFixed(0)}s   `);
}

/* =====================================================================
 * FAST 模式：CDP 长连接
 * ===================================================================== */

class CdpSession {
  constructor(ws, sessionId, idAlloc){
    this.ws = ws; this.sessionId = sessionId; this.idAlloc = idAlloc;
    this.pending = new Map();     // id -> {resolve, reject}
    this.eventWaiters = [];       // {method, resolve}
    ws.addEventListener('message', ev => this._onMessage(String(ev.data)));
  }
  _onMessage(raw){
    let msg; try { msg = JSON.parse(raw); } catch { return; }
    if (msg.id !== undefined && this.pending.has(msg.id)){
      // 响应必须来自自己的会话（id 全局唯一的前提下这是双保险）
      if (msg.sessionId !== undefined && this.sessionId !== undefined && msg.sessionId !== this.sessionId) return;
      const p = this.pending.get(msg.id);
      this.pending.delete(msg.id);
      msg.error ? p.reject(new Error(msg.error.message || 'CDP error'))
                : p.resolve(msg.result);
    } else if (msg.method && (!msg.sessionId || msg.sessionId === this.sessionId)){
      this.eventWaiters = this.eventWaiters.filter(w => {
        if (w.method === msg.method){ w.resolve(msg.params); return false; }
        return true;
      });
    }
  }
  send(method, params = {}){
    return new Promise((resolve, reject) => {
      const id = this.idAlloc();          // 全局唯一：跨会话绝不碰撞
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params, sessionId: this.sessionId }));
      setTimeout(() => {
        if (this.pending.has(id)){
          this.pending.delete(id);
          reject(new Error(`CDP ${method} 超时`));
        }
      }, 30000);
    });
  }
  waitEvent(method, timeoutMs = 30000){
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`等待事件 ${method} 超时`)), timeoutMs);
      this.eventWaiters.push({ method, resolve: p => { clearTimeout(timer); resolve(p); } });
    });
  }
}

async function fastMode(){
  // 1. 启动一个带 remote-debugging 的 Chrome
  const profile = join(os.tmpdir(), `opusrender-fast-${process.pid}`);
  const args = [
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--mute-audio',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--allow-file-access-from-files',
    '--force-device-scale-factor=1',
    '--no-proxy-server',
    `--window-size=${WIDTH},${HEIGHT}`,
    '--remote-debugging-port=0',
    `--user-data-dir=${profile}`,
    'about:blank'
  ];
  const proc = spawn(CHROME, args, { stdio: ['ignore', 'ignore', 'pipe'] });
  let stderrBuf = '';
  const wsUrl = await new Promise((res, rej) => {
    const timer = setTimeout(() => rej(new Error('Chrome 未在 20s 内输出 DevTools 端口')), 20000);
    proc.stderr.on('data', d => {
      stderrBuf += d.toString();
      const m = stderrBuf.match(/DevTools listening on (ws:\/\/\S+)/);
      if (m){ clearTimeout(timer); res(m[1]); }
    });
    proc.on('exit', code => { clearTimeout(timer); rej(new Error(`Chrome 提前退出 code=${code}\n${stderrBuf}`)); });
  }).catch(e => { try { proc.kill(); } catch {} throw e; });
  const tChrome = ((Date.now() - t0) / 1000).toFixed(1);

  // 2. 连 WebSocket（Node 22+ 全局 WebSocket）
  if (typeof WebSocket === 'undefined'){
    try { proc.kill(); } catch {}
    throw new Error('当前 Node 无全局 WebSocket（需要 Node ≥22），请用 --slow 或升级 Node');
  }
  const ws = new WebSocket(wsUrl);
  await new Promise((res, rej) => {
    ws.addEventListener('open', res, { once: true });
    ws.addEventListener('error', () => rej(new Error('WebSocket 连接失败')), { once: true });
  });
  ws.addEventListener('error', () => {});   // 防未处理异常打断主流程

  const browser = new CdpSession(ws, undefined, () => idSeq++);
  let idSeq = 1;   // 全局唯一 id 分配器：所有会话共用，防止跨会话响应错投

  // 3. 开 N 个并行会话
  async function openSession(){
    const { targetId } = await browser.send('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await browser.send('Target.attachToTarget', { targetId, flatten: true });
    const s = new CdpSession(ws, sessionId, () => idSeq++);
    await s.send('Page.enable');
    await s.send('Runtime.enable');
    // 强制视口尺寸：headless 窗口含边框，captureScreenshot 抓的是布局视口，
    // 不锁视口会得到 1896x981 这类被吃掉边框的尺寸
    await s.send('Emulation.setDeviceMetricsOverride',
      { width: WIDTH, height: HEIGHT, deviceScaleFactor: 1, mobile: false });
    return s;
  }

  async function shootFast(s, job){
    const tStr = job.t.toFixed(4);
    const url = `${URL_BASE}?t=${tStr}`;
    const loaded = s.waitEvent('Page.loadEventFired', 25000).catch(() => {});
    await s.send('Page.navigate', { url });
    await loaded;
    // 等 READY 且确认评的是新文档：loadEventFired 后旧文档可能还活着，
    // 它的 READY 也是 true —— 不校验 location.search 会截到上一帧（竞态实录）
    const deadline = Date.now() + 8000;
    while (Date.now() < deadline){
      try {
        const r = await s.send('Runtime.evaluate', {
          expression: `window.READY === true && location.search === "?t=${tStr}"`,
          returnByValue: true
        });
        if (r && r.result && r.result.value === true) break;
      } catch {}
      await new Promise(r2 => setTimeout(r2, 30));
    }
    await new Promise(r2 => setTimeout(r2, 50));   // 等合成器把画布提交到截图表面
    const shot = await s.send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(job.file, Buffer.from(shot.data, 'base64'));
    if (!existsSync(job.file) || statSync(job.file).size < 2000) throw new Error(`帧 t=${job.t} 截图异常`);
  }

  let cursor = 0;
  async function worker(){
    const s = await openSession();
    try {
      while (cursor < jobs.length){
        const job = jobs[cursor++];
        for (let attempt = 0; attempt < 3; attempt++){
          try { await shootFast(s, job); break; }
          catch (e){ if (attempt === 2){ failed++; console.error(`\n  ✗ t=${job.t.toFixed(2)} ${e.message}`); } }
        }
        done++; progress();
      }
    } finally {
      try { await browser.send('Target.closeTarget', { targetId: s.targetId }); } catch {}
    }
  }

  try {
    console.log(`\n模式：fast（CDP 复用浏览器，${Math.min(CONC, jobs.length)} 会话并行）  Chrome 启动 ${tChrome}s`);
    await Promise.all(Array.from({ length: Math.min(CONC, jobs.length) }, worker));
  } finally {
    try { ws.close(); } catch {}
    try { proc.kill(); } catch {}
    const tTear = Date.now();
    try { rmSync(profile, { recursive: true, force: true }); } catch {}
    console.log(`  （teardown ${( (Date.now() - tTear) / 1000).toFixed(1)}s）`);
  }
}

/* =====================================================================
 * LEGACY 模式：每帧一个 Chrome 进程
 * ===================================================================== */

function shoot(t, file){
  return new Promise((resolvePromise, reject) => {
    const tmpProfile = join(os.tmpdir(), `opusrender-${process.pid}-${Math.round(t * 1000)}-${Math.random().toString(36).slice(2, 7)}`);
    const args = [
      '--headless=new',
      '--disable-gpu',
      '--hide-scrollbars',
      '--mute-audio',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-extensions',
      '--allow-file-access-from-files',
      '--force-device-scale-factor=1',
      `--window-size=${WIDTH},${HEIGHT}`,
      `--virtual-time-budget=${BUDGET}`,
      `--user-data-dir=${tmpProfile}`,
      `--screenshot=${file}`,
      `${URL_BASE}?t=${t.toFixed(4)}`
    ];
    const p = spawn(CHROME, args, { stdio: 'ignore' });
    const timer = setTimeout(() => { p.kill(); }, 60000);
    p.on('error', reject);
    p.on('exit', () => {
      clearTimeout(timer);
      try { rmSync(tmpProfile, { recursive: true, force: true }); } catch {}
      let ok = false;
      try { ok = existsSync(file) && statSync(file).size > 2000; } catch {}
      ok ? resolvePromise() : reject(new Error(`帧 t=${t} 截图失败`));
    });
  });
}

async function legacyMode(){
  console.log(`\n模式：legacy（每帧独立 Chrome 进程，并发 ${CONC}）`);
  let cursor = 0;
  async function worker(){
    while (cursor < jobs.length){
      const job = jobs[cursor++];
      for (let attempt = 0; attempt < 3; attempt++){
        try { await shoot(job.t, job.file); break; }
        catch (e){ if (attempt === 2){ failed++; console.error(`\n  ✗ t=${job.t.toFixed(2)} ${e.message}`); } }
      }
      done++; progress();
    }
  }
  await Promise.all(Array.from({ length: Math.min(CONC, jobs.length) }, worker));
}

/* ---------- 主流程 ---------- */
async function main(){
  if (USE_FAST){
    try {
      await fastMode();
    } catch (e){
      console.error(`\n[!] fast 模式失败：${e.message}`);
      console.error('[!] 自动回退 legacy 模式重跑全部任务…');
      done = 0; failed = 0;
      await legacyMode();
    }
  } else {
    await legacyMode();
  }
  console.log(`\n${failed ? '⚠' : '✓'} 完成：${jobs.length - failed} 成功 / ${failed} 失败  → ${OUT}`);
  if (!STILLS) console.log(`\n下一步合成视频：\n  powershell -File build.ps1\n  或 bash build.sh`);
  if (failed > 0 && failed === jobs.length) process.exit(1);
}

main().catch(e => { console.error(e); process.exit(1); });
