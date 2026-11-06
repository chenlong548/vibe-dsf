#!/usr/bin/env node
/* review.mjs — 静帧并排评审页生成器（P1 #9）
 * 把一条片的场景结构 + 采样静帧生成单文件 review.html：7 章一屏看齐，人工挑卡点/比风格。
 * A/B 模式：--compare 给第二条片，按 segment 对齐并排（定风格抽卡最常用）。
 *
 * 用法：
 *   node pipeline/review.mjs --project projects/demo-hook-compound
 *   node pipeline/review.mjs --project projects/a --compare projects/b
 * 产物：<project>/review.html（图片相对引用 frames/，不复制文件）
 * 依赖：项目目录里有 SCENE-PLAN.json + frames/frame_*.png（先渲染）。
 */
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const get = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const projA = get('--project');
const projB = get('--compare');
if (!projA) { console.error('用法: node review.mjs --project <dir> [--compare <dirB>]'); process.exit(2); }

const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function loadProject(dir) {
  const planPath = path.join(dir, 'SCENE-PLAN.json');
  if (!fs.existsSync(planPath)) { console.error(`[review] ${dir} 没有 SCENE-PLAN.json`); process.exit(1); }
  const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  const meta = plan.meta || {};
  // palette 可能是引用制（G7）——评审页只需要 accent 做点缀，缺省给中性色
  let accent = '#E8A87C';
  try {
    if (!meta.palette && meta.palette_name) {
      const brand = JSON.parse(fs.readFileSync(path.join(__dirname(), 'palette.json'), 'utf8'));
      const p = brand.palettes[meta.palette_name] || {};
      accent = p.accent || accent;
    } else if (meta.palette) accent = meta.palette.accent || accent;
  } catch { /* 缺 palette.json 就用默认 */ }
  const fps = meta.fps || 30;
  const framesDir = path.join(dir, 'frames');
  const scenes = (plan.scenes || []).map(sc => {
    const dur = Math.max(0.01, (sc.t_out ?? 0) - (sc.t_in ?? 0));
    const samples = [sc.t_in + 0.05, sc.t_in + dur / 2, sc.t_out - 0.05]
      .map(t => ({ t, f: Math.max(1, Math.round(t * fps)) }))
      .map(({ t, f }) => ({
        t, f,
        file: `frame_${String(f).padStart(5, '0')}.png`,
        exists: fs.existsSync(path.join(framesDir, `frame_${String(f).padStart(5, '0')}.png`)),
      }));
    const subs = (plan.subtitles || []).filter(s => s.t_in >= sc.t_in - 0.01 && s.t_in < sc.t_out).length;
    return {
      id: sc.id, segment: sc.segment, t_in: sc.t_in, t_out: sc.t_out,
      block: sc.l2?.block || '—', area: sc.l2?.area_pct, subtitles: subs,
      samples,
    };
  });
  return { dir, name: path.basename(path.resolve(dir)), meta, accent, scenes,
           hasFrames: fs.existsSync(framesDir) };
}

function __dirname() { return path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1'); }

function sceneCard(sc, imgPrefix, accent, dialogId) {
  const seg = esc(sc.segment);
  const shots = sc.samples.map(s => s.exists
    ? `<img loading="lazy" src="${imgPrefix}frames/${s.file}" data-full="${imgPrefix}frames/${s.file}"
         onclick="D.showModal();document.getElementById('big').src=this.dataset.full"
         title="t=${s.t.toFixed(2)}s → ${s.file}">`
    : `<div class="miss" title="${s.file} 不存在">缺帧<br><small>${s.file}</small></div>`).join('');
  return `<div class="card">
    <div class="head"><span class="sid">${esc(sc.id)}</span><span class="seg s-${seg}">${seg}</span>
      <span class="time">${sc.t_in.toFixed(2)}–${sc.t_out.toFixed(2)}s</span></div>
    <div class="meta"><code>${esc(sc.block)}</code>${sc.area ? ` · area ${(sc.area * 100).toFixed(0)}%` : ''} · 字幕×${sc.subtitles}</div>
    <div class="shots">${shots}</div></div>`;
}

function buildPage(A, B) {
  const accentA = esc(A.accent), accentB = B ? esc(B.accent) : accentA;
  const col = (P, prefix, tag, accent) => `
    <div class="col">
      <div class="ptitle" style="border-color:${accent}"><b>${esc(P.name)}</b>
        <span class="pmeta">${esc(P.meta.topic || '')} · ${(P.meta.duration || 0).toFixed(2)}s @ ${P.meta.fps}fps
        · ${P.meta.style || ''}${P.meta.palette_name ? ` · ${esc(P.meta.palette_name)}` : ''}</span>
        <span class="tag">${tag}</span></div>
      ${P.scenes.map(sc => sceneCard(sc, prefix, accent)).join('\n')}
    </div>`;
  const segAlign = B ? `
    <p class="hint">A/B 按 segment 对齐：上=${esc(A.name)}，下=${esc(B.name)}（勾掉一侧可独看）</p>
    ${A.scenes.map((sc, i) => {
      const b = B.scenes[i] || null;
      const row = (P, sc2, prefix, cls, accent) => sc2
        ? `<div class="half ${cls}">${sceneCard(sc2, prefix, accent)}</div>` : '<div class="half empty">（此侧无对位场景）</div>';
      return `<div class="pair"><div class="pairhead">PAIR ${i + 1} · ${esc(sc.segment)}（A ${sc.t_in.toFixed(2)}s / B ${b ? b.t_in.toFixed(2) : '—'}s）</div>
        ${row(A, sc, '', 'a', accentA)}${row(B, b, `../${esc(B.name)}/`, 'b', accentB)}</div>`;
    }).join('\n')}` : '';
  const body = B ? segAlign : col(A, '', 'A', accentA);
  const title = B ? `${A.name} vs ${B.name}` : A.name;
  return `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>评审 · ${esc(title)}</title>
<style>
  :root{color-scheme:dark}
  body{margin:0;background:#141416;color:#e8e8ea;font:14px/1.5 "Microsoft YaHei",sans-serif;padding:20px}
  h1{font-size:18px;margin:0 0 4px}.hint{color:#9a9aa2;margin:6px 0 14px;font-size:12px}
  .grid{display:grid;grid-template-columns:1fr;gap:14px}
  .card{background:#1d1d21;border:1px solid #2c2c31;border-radius:10px;padding:10px 12px;margin-bottom:12px}
  .head{display:flex;gap:10px;align-items:baseline;margin-bottom:4px}
  .sid{font-weight:700;font-size:15px}
  .seg{font-size:11px;padding:1px 8px;border-radius:99px;background:#2c2c31}
  .s-hook{background:#5c3a1e}.s-anchor{background:#1e3a5c}.s-reason{background:#1e5c3a}.s-turn{background:#5c1e38}.s-land{background:#3a5c1e}
  .time{color:#9a9aa2;font-size:12px;margin-left:auto}
  .meta{color:#9a9aa2;font-size:12px;margin-bottom:8px}code{color:#d0d0d6}
  .shots{display:flex;gap:8px}
  .shots img{width:calc((100% - 16px)/3);aspect-ratio:16/9;object-fit:cover;border-radius:6px;cursor:zoom-in;background:#000}
  .shots img:hover{outline:2px solid ${accentA}}
  .miss{width:calc((100% - 16px)/3);aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;
        background:#232327;color:#6a6a72;border-radius:6px;font-size:11px;text-align:center}
  /* A/B 模式 */
  .pair{margin-bottom:18px}.pairhead{color:#9a9aa2;font-size:12px;margin-bottom:6px;letter-spacing:.5px}
  .half.a{border-left:3px solid ${accentA}}.half.b{border-left:3px solid ${accentB}}
  .empty{color:#6a6a72;padding:20px;background:#1a1a1e;border-radius:8px;font-size:12px}
  .ptitle{border-left:3px solid;padding:6px 10px;background:#1d1d21;border-radius:0 8px 8px 0;margin-bottom:14px}
  .pmeta{color:#9a9aa2;font-size:12px;margin-left:8px}.tag{float:right;color:#6a6a72;font-size:11px}
  dialog{background:#111114;color:#eee;border:1px solid #333;border-radius:10px;max-width:92vw;padding:8px}
  dialog img{max-width:90vw;max-height:82vh;display:block}
  dialog::backdrop{background:rgba(0,0,0,.75)}
  .close{color:#9a9aa2;font-size:12px;cursor:pointer;float:right;padding:2px 6px}
</style></head><body>
<h1>静帧评审 · ${esc(title)}</h1>
<p class="hint">场景结构来自 SCENE-PLAN.json；每场景采样 t_in+0.05 / 中点 / t_out-0.05 三帧。点图放大。缺帧 = 该时刻未渲染。</p>
${body}
<dialog id="D"><span class="close" onclick="D.close()">关闭 ✕</span><img id="big" alt=""></dialog>
</body></html>`;
}

const A = loadProject(projA);
const B = projB ? loadProject(projB) : null;
if (!A.hasFrames) console.error(`[review] 警告: ${A.dir}/frames 不存在——产物全是缺帧占位（先渲染）`);
const html = buildPage(A, B);
const out = path.join(A.dir, 'review.html');
fs.writeFileSync(out, html, 'utf8');
const kb = (html.length / 1024).toFixed(1);
console.log(`[review] ${A.scenes.length} 场景${B ? ` ×2 (A/B: ${A.name} vs ${B.name})` : ''} -> ${out} (${kb} KB)`);
