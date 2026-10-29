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

const needed = [...new Set(plan.scenes.map(s => s.l2 && s.l2.block).filter(Boolean))];
const missing = needed.filter(n => !regMap[n]);
if (missing.length) {
  console.error(`[build_html] 未注册积木: ${missing.join(', ')}（先过 QA 入库）`);
  process.exit(1);
}

const src = needed.map(n => fs.readFileSync(path.join(blocksRoot, 'lib', n + '.js'), 'utf8')).join('\n\n');

let html = fs.readFileSync(path.join(here, 'template.html'), 'utf8');
html = html
  .replace('{{TITLE}}', String(plan.meta.topic))
  .replace('{{BLOCKS_JS}}', src)
  .replace('{{PLAN_JSON}}', JSON.stringify(plan).replace(/</g, '\\u003c'));

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, html, 'utf8');
console.log(`[build_html] 积木 [${needed.join(', ')}] -> ${outPath} (${(html.length / 1024).toFixed(1)} KB)`);
