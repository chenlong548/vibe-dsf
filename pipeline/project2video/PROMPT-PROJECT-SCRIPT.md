# PROMPT · 项目片规划任务书（PROJECT-BRIEF → SCENE-PLAN）

> **给谁用**：任何 LLM。喂给它三样东西：本文件 + `pipeline/scene_writer/PROMPT.md` + 过闸的 PROJECT-BRIEF.json。
> **解决什么**：brief 是"介绍什么"，SCENE-PLAN 是"怎么画、怎么念、卡什么点"。
> 本任务书写**项目介绍片的特化规则**；通用硬约束（拍点/密度/构图/字幕）全部沿用 scene_writer/PROMPT.md。

---

## 风格契约（paper · 与个人独立站同源的设计语言）

| 项 | 值 |
|---|---|
| `meta.style` | `"paper"`（浅底模式：无星空、墨色纸纹、浅墨影边缘） |
| `meta.pattern` | `"hairline"`（teal 发丝线正交网格，图纸感） |
| `meta.palette_name` | **推荐：`"paper"`**——整套已验证配色（下表全部键）+ style + pattern 一次引用生效，见 `pipeline/palette.json`；下表逐键内联仅在新调色时用 |
| `palette.bg_in / bg_out` | `"#fcfcfa"` / `"#f2f1ec"`（暖白纸面渐变） |
| `palette.ink / gray` | `"#16181c"` / `"#666c74"` |
| `palette.accent` | `"#0d6e63"`（deep teal——独立站唯一强调色，刻意不用蓝） |
| `palette.surface / line / sunken` | `"#ffffff"` / `"#e6e5e1"` / `"#f4f4f1"`（卡面/发丝线/凹陷面） |
| `palette.dim` | `"102,108,116"`（顶栏杂色 rgb 基色） |
| `palette.sub_en` | `"#7c828b"`（英文字幕行） |
| `palette.term_*` | term_bg `"#0e1214"`、term_line `"#242c30"`、term_ink `"#d6dde1"`、term_dim `"#7c878e"`、term_accent `"#5ed3b8"`、term_amber `"#e3b341"`（终端证据窗专用） |

设计哲学（照抄独立站）：**浅面为主，暗色终端面板只装技术证据；唯一强调色省着用——它标记可行动的东西**（命中、成功、CTA）。

## 叙事映射（brief → 五段）

| 段位 | 装什么 | 取自 brief | 积木直觉 |
|---|---|---|---|
| hook | 旧做法成本 vs 新做法成本，对撞开场 | pain.old_way_cost + hook_candidates[0] | `vs-counters`（左旧右新，右染 teal） |
| anchor | 一句话定位 + 身份标签（它是什么） | meta.one_liner + features 名字 | `text-points` 或 `feature-cards` |
| reason | 终端实况（证据窗）→ 特性逐个点亮 | quickstart → `terminal-window`；features → `feature-cards` | 证据先行，命令必须贴 README 原文 |
| turn | 质量数字 + 边界诚实 | metrics[0] → `beat-counter`；limits 进 l3 | "不过闸不出片"式的纪律反转 |
| land | repo + 语言 chips + 一行安装命令 | cta → `repo-card` | 可行动收口：install 是 teal 的舞台 |

典型 6 场景 50s（126BPM=105 拍整）：hook 16 拍 / anchor 18 / reason 26 / reason 25 / turn 11 / land 9。
时长 40-70s 自适应时，先定拍数（duration = beats × 60/bpm）再拆段。

## 项目片特化纪律

1. **数字只从 brief 取**：metrics/quickstart 里没有的数字（stars、用户量）不许上画面——
   repo-card 不给 stars 就显示语言行，宁缺毋编。
2. **终端命令 = README 原文**：terminal-window 的 cmd/out 行必须是 brief.quickstart 的原文摘录，
   输出行可以摘真实 gate/构建日志，不许编造成功信息。
3. **limits 最狠的一条给 turn 或字幕**：项目片的可信度来自敢说做不到什么。
4. **proof 不够硬的特性不上片**：feature-cards 的 sub 写 proof 的口语版，不是形容词。
5. **术语配 mono 标注**：repo 名、命令、文件路径进 l3 时 `mono: true`，版本感。
6. **旁白更短促**：项目片每句 ≤20 字（读法音节 × 4.5 音节/秒估窗规则不变），
   语气是"演示"不是"讲课"——设问少，直接上证据。

## 积木选型直觉（项目叙事件 → 积木）

| 项目里有什么 | 用什么积木 |
|---|---|
| 旧做法 vs 新做法的成本反差 | `vs-counters` |
| 一句话定位 / 身份清单 | `text-points` |
| 安装、构建、闸门日志（证据） | `terminal-window` |
| 3-6 个核心特性逐个亮相 | `feature-cards` |
| 质量分 / 性能数字 / 规模 | `beat-counter` |
| repo 收口 + CTA | `repo-card` |
| 仓库演化 / 版本历史 | `timeline` |

## 输出格式

只输出一个 JSON 代码块（SCENE-PLAN.json 全文，`meta.style: "paper"`）。
被 validate_plan.py 打回时只修违规项。
