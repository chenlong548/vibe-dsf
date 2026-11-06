#!/usr/bin/env node
/* build_html.mjs — SCENE-PLAN → 单文件 index.html
 * 把 template.html、所选 blocks 积木源码、SCENE-PLAN.json 组装成符合
 * render(t) 契约的自包含 HTML（flash/人都不用手写场景代码）。
 * 用法：node build_html.mjs --plan <SCENE-PLAN.json> --out <projects/x/index.html> */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const get = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };

const planPath = get('--plan');
const outPath = get('--out');
if (!planPath || !outPath) {
  console.error('用法: node build_html.mjs --plan <SCENE-PLAN.json> --out <projects/x/index.html>');
  process.exit(2);
}

const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
const blocksRoot = path.join(here, '..', 'blocks');
const registry = JSON.parse(fs.readFileSync(path.join(blocksRoot, 'registry.json'), 'utf8'));
const regMap = Object.fromEntries(registry.blocks.map(b => [b.name, b]));

/* ---- 品牌契约物化（G7）：palette_name 引用 / 内联 palette / 默认值 三层优先级 ----
 * 内联 meta.palette > meta.palette_name（引用 pipeline/palette.json）> default_palette。
 * watermark 缺省取 brand.watermark。解析结果直接写回 plan.meta——template.html 零感知。 */
const palettePath = path.join(here, '..', 'palette.json');
if (fs.existsSync(palettePath)) {
  const brand = JSON.parse(fs.readFileSync(palettePath, 'utf8'));
  const M = plan.meta;
  if (!M.palette && M.palette_name) {
    const p = brand.palettes[M.palette_name];
    if (!p) { console.error(`[build_html] palette_name "${M.palette_name}" 不在 pipeline/palette.json（可用: ${Object.keys(brand.palettes).join(', ')}）`); process.exit(1); }
    const { _from, ...colors } = p;
    M.palette = colors;
    if (!M.style && colors.style) M.style = colors.style;
    if (!M.pattern && colors.pattern) M.pattern = colors.pattern;
  }
  if (!M.palette && brand.default_palette && brand.palettes[brand.default_palette]) {
    const { _from, ...colors } = brand.palettes[brand.default_palette];
    M.palette = colors;
    if (!M.style && colors.style) M.style = colors.style;
    if (!M.pattern && colors.pattern) M.pattern = colors.pattern;
    console.log(`[build_html] palette 未指定，回落 default_palette "${brand.default_palette}"`);
  }
  if (!M.watermark && brand.brand && brand.brand.watermark) M.watermark = brand.brand.watermark;
}

const needed = [...new Set(plan.scenes.map(s => s.l2 && s.l2.block).filter(Boolean))];
const missing = needed.filter(n => !regMap[n]);
if (missing.length) {
  console.error(`[build_html] 未注册积木: ${missing.join(', ')}（先过 QA 入库）`);
  process.exit(1);
}

const src = needed.map(n => fs.readFileSync(path.join(blocksRoot, 'lib', n + '.js'), 'utf8')).join('\n\n');
/* 缓动预设集（P1 #10）：下划线开头 = 非积木基础设施，恒定注入（不进 registry） */
const easeSrc = fs.readFileSync(path.join(blocksRoot, 'lib', '_easings.js'), 'utf8');

let html = fs.readFileSync(path.join(here, 'template.html'), 'utf8');
/* 替换值一律用函数形式：字符串形式的 replacement 会把 $'/$&/$` 当特殊序列，
 * 积木里的终端提示符 '$' 曾把模板后半段整个插进代码（repo-card 截断事故） */
html = html
  .replace('{{TITLE}}', () => String(plan.meta.topic))
  .replace('{{EASE_JS}}', () => easeSrc)
  .replace('{{BLOCKS_JS}}', () => src)
  .replace('{{PLAN_JSON}}', () => JSON.stringify(plan).replace(/</g, '\\u003c'));

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, html, 'utf8');
console.log(`[build_html] 积木 [${needed.join(', ')}] -> ${outPath} (${(html.length / 1024).toFixed(1)} KB)`);
