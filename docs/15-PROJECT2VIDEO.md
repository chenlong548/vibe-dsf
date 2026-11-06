# 15 · PROJECT2VIDEO：GitHub 项目 → 项目介绍视频（独立风格线）

> 解决什么：介绍 GitHub 项目的视频和讲理论的视频**不应该是同一种语言**。
> 理论片（docs/14）是"深空冷底 × 暖橙爆点"的宇宙感；项目片是"纸面 + 墨字 + teal 强调 +
> 终端证据窗"的工作台感——设计语言与个人独立站同源（site 的 globals.css 设计令牌）。
> 拆解层换任务书，后半程（组装/渲染/QA/旁白/BGM/合成）100% 复用。

---

## 一、风格契约（paper · 模板已参数化）

模板 `scene_writer/template.html` 由 `meta.style` 切肤；**深空片零改动**（默认值 = 原行为，回归已验证）。

| 项 | paper 值 | 说明 |
|---|---|---|
| `meta.style` | `"paper"` | 浅底模式：无星空、墨色纸纹 GRAIN、浅墨影边缘（不做暗角） |
| `meta.pattern` | `"hairline"` | teal 发丝线正交网格（图纸感，近静止，运动由萤火层承担） |
| palette 主四色 | `#fcfcfa/#f2f1ec` 底 · `#16181c` 墨 · `#666c74` 灰 · `#0d6e63` 强调 | deep teal，独立站唯一强调色 |
| palette 扩展 | `surface #ffffff` · `line #e6e5e1` · `sunken #f4f4f1` · `dim "102,108,116"` · `sub_en "#7c828b"` | 卡面/发丝线/凹陷面/顶栏杂色/英文字幕 |
| palette.term_* | `#0e1214 / #242c30 / #d6dde1 / #7c878e / #5ed3b8 / #e3b341` | 终端证据窗专用（暗面板只装证据） |

设计哲学照抄独立站：**浅面为主；暗色面板只装技术证据；唯一强调色省着用——标记可行动的东西**。

## 二、全链路

```
README.md ──(① PROMPT-PROJECT.md × 任何 LLM)
              PROJECT-BRIEF.json ──(validate_brief_project.py：特性带证据/钩子有反差素材/limits≥1)
              │
              ▼ ② PROMPT-PROJECT-SCRIPT.md + scene_writer/PROMPT.md
              SCENE-PLAN.json（meta.style="paper"）──(validate_plan.py 同一套硬闸)
              │
              ▼ ③ build_html.mjs → 渲染 → QA 门禁 → run_all.ps1（旁白+BGM+合成）
              final.mp4
```

| 层 | 文件 | 产出 | 项目片特化 |
|---|---|---|---|
| 拆解 | `project2video/PROMPT-PROJECT.md` | PROJECT-BRIEF.json | features[].**proof 必填**（防吹牛）、pain.old_way_cost 供对撞钩子 |
| 规划 | `project2video/PROMPT-PROJECT-SCRIPT.md` | SCENE-PLAN.json | 数字只从 brief 取（stars 没有就不显示）、终端命令=README 原文 |
| 闸 | `project2video/validate_brief_project.py` | — | 拦"结构性吹牛"：没证据的特性、没来源的数字、没边界的自夸 |

## 三、叙事映射（项目五段）

| 段位 | 装什么 | 积木 |
|---|---|---|
| hook | 旧做法成本 vs 新做法成本 | `vs-counters`（右染 teal；支持 prefix/suffix） |
| anchor | 一句话定位 + 身份清单 | `text-points` |
| reason | 终端实况 → 特性逐个点亮 | `terminal-window` → `feature-cards` |
| turn | 质量数字 + 边界诚实 | `beat-counter`（limits 进字幕） |
| land | repo + chips + 一行安装命令 | `repo-card`（stars 未知就显示语言行，宁缺毋编） |

时长建议 40-70s（126BPM 拍网格：50.0s = 105 拍整）。典型 6 场景。

## 四、项目片积木（paper 风格）

- **feature-cards**：白卡 + 发丝线框 + 墨影，命中 = teal 顶条拉满 + easeOutBack 上浮；
  卡底进度线自命中填充到场景尾 + teal 巡游光带沿卡行横扫（持续运动源）
- **terminal-window**：暗面板嵌浅底，三圆点标题栏；cmd 行 `$` teal + 逐字敲入 + 块光标呼吸；
  ok/warn 着色；0.18s 快入场 + CRT 扫描光带 + 底部 barber-pole 执行进度条
- **repo-card**：owner（灰）/name（墨）等宽大字 + 星数滚动（可关）+ 语言胶囊 +
  `$` 安装命令逐字敲入（打完只剩终端光标闪烁）+ 静态 teal 描边

> **强调语言（2026-11-06 用户定调，全积木适用）**：数字/圆点落定后绝对静止——禁止
> 呼吸、伸缩、脉冲、闪烁；强调 = 落定下划线一次性扫出后静态保持；运动感交给巡游光带。
> **运动源铁律**（详见 blocks/README.md）：细线/微脉冲凑不够 QA 的 0.35%/帧变化底线，
> 长场景必须配大面积匀速平移的光带；入场淡入 >0.4s 会被计成连续"硬切"。

## 五、首条实测：vibe-dsf 自举（50s，projects/project-vibe-dsf/）

用项目线介绍项目线自己。数字全部来自本仓库真实产物（0.13s/帧、QA 9.5/10、11 组检查）。

- brief 双闸：一次过；plan：一轮修复（l3 数量/拍点网格/字号下限——机器闸的价值又在）
- 旁白 11 句：两句超窗（顿号停顿被低估），**加窗不压速**修复后零警告零截断
- 视觉探针 4 帧目检：抓出 3 处 l3 与字幕带相撞，全部移位修复
- **事故与修复（重要 bug 档案）**：`build_html.mjs` 的 `String.replace` 字符串替换把积木代码里的
  终端提示符 `'$'` 当成特殊序列 `$'`（"插入匹配后面的全部文本"），把模板后半段整个插进了代码，
  页面直接黑屏。修复：三处替换全部改函数形式 `replace(x, () => value)`（字面替换）。
  **凡 replace 的 replacement 可能含 `$` 的地方，一律函数形式。**
- 渲染：1500 帧 fast 模式 ~15-20 min
- **QA 7.4 → 8.5 一轮治理（四个坑全是新知识，已沉淀进积木）**：
  ① 静止控制 4：终端打完字后 10.8s 死寂 + 卡片弹入后 4.86s → 三积木加持续运动源
    （扫描带/barber-pole 进度条/巡游光带/卡底进度线）——**细线没有面积，光带才够 0.35%/帧**；
  ② 安全区 5：`edge_bleed` 列表有 `[:10]` 显示截断，**全部 1500 帧都过线**——paper 浅底
    亮度 252 在暗角 α≈0 处恒 >235 → 浅底暗角加强（边中点 α0.086→亮度 232，只动 LIGHT 分支）；
  ③ 切点节奏：8 连"硬切"其实是终端 0.5s 慢淡入（δα≈0.2/帧连续 8 帧超 25% 画幅阈值）→
    入场统一 ≤0.2s，一次弹现只计 1-2 切；
  ④ 断点 5 仍弱（S2 点亮间隙 ~1.7s×3）：demo 用的旧版 text-points，新光带版下次自动受益。

## 六、命令速查（项目片全流程）

```bash
# ① 喂 PROMPT-PROJECT.md + README 给 LLM → PROJECT-BRIEF.json
python pipeline/project2video/validate_brief_project.py projects/<slug>/PROJECT-BRIEF.json
# ② 喂 PROMPT-PROJECT-SCRIPT.md + scene_writer/PROMPT.md + brief 给 LLM → SCENE-PLAN.json
python pipeline/scene_writer/validate_plan.py projects/<slug>/SCENE-PLAN.json
node pipeline/scene_writer/build_html.mjs --plan projects/<slug>/SCENE-PLAN.json --out projects/<slug>/index.html
cd projects/<slug>
node ../../pipeline/render_frames.mjs --duration 50 --fps 30        # 全量；--stills 20,36 定风格
python ../../pipeline/qa_check.py frames/ --fps 30                  # 门禁 ≥8
python ../../pipeline/narrate/build_narration.py SCENE-PLAN.json --out narration.wav --rate "+15%"
python ../../pipeline/synth_bgm.py bgm.wav --style vibe --bpm 126 --duration 50 --seed <n> --marks "<卡点>"
python ../../pipeline/narrate/mix_audio.py --narration narration.wav --bgm bgm.wav --duration 50 --out final_audio.wav
# 合成见 build.ps1（-Audio final_audio.wav，内部 loudnorm -14 LUFS）
```

## 七、后续

- 系列 template：同一项目 hook 片 + 深讲片 + 项目片三连发，brief 互通
- terminal-window 增强：实时 gate 输出对接（真跑 run_all 抓日志进画面）
- 独立站 work 页嵌入成片：站点 case-study 与项目片一一对应
