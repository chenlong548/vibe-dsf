# 更新日志（CHANGELOG）

本项目的版本号为语义化版本（SemVer：MAJOR.MINOR.PATCH）。
**纪律：每一次推送到 GitHub 都递增版本 + 在本文件记录 + 打同名 tag。**
版本判定：新功能/工具增强 → MINOR；修 bug/文档同步 → PATCH；破坏性改动（渲染契约、plan 格式不兼容）→ MAJOR。

## [1.4.0] - 2026-11-06

### Added
- **一键流水线执行报告**（`pipeline/report/generate.py`，`docs/21-PIPELINE-REPORT.md`）：
  每次 `run_all.ps1` 运行（成功或失败）都在项目目录产出 `pipeline_report.json` ——
  阶段耗时/状态/退出码、QA 摘要与最弱三项、帧数与分辨率、8 类产物字节数、
  plan 摘要（场景/字幕/旁白/SFX）、失败阶段定位。事件原流 append-only 保存在
  `_pipeline_events.jsonl`，中途崩溃也能留档。
- `run_all.ps1` 的 12 处裸 `exit` 收敛为统一出口 `Complete-Report`，各阶段独立 Stopwatch
  计时；新增 `-NoReport` 应急开关。报告生成失败恒定返回 0，绝不改变流水线退出码。
- **回归夹具** `pipeline/report/test_generate.py`：8 条断言（成功形状 / QA 拦截 / 早期失败 /
  合成失败 / 坏事件行 / 缺产物 / CLI 中文往返 / append-only 顺序），已接入 CI。

### Design
- PowerShell 不拼 JSON：PS 5.1 的 `ConvertTo-Json` 有 BOM / 中文 `\uXXXX` 转义 /
  单元素数组退化等坑；PS 只传 6 个标量，结构化与目录扫描全交给 Python。
- 报告是**观测**，不是门禁：`avg<8` 仍只由 `pipeline/qa/qa_check.py` 拦截。

### Verified
- 成功路径 demo-hook-compound `-SkipRender`：exit 0 / 5 阶段（4 ok + 1 skipped）/
  57.85s / QA 8.82 (v4) / 8 类产物全在位；`qa 32.67s` 为最慢阶段。
- 失败路径 30 帧全黑夹具：exit 2 / `verdict=qa_blocked` / `failed_stage=qa` /
  QA 6.55 / 产物只剩 html + qa.json（后续阶段确实未跑）。
- `run_all.ps1` BOM=True / PSParser 0 错；两个回归夹具共 15 条断言全绿。

### Docs
- 新增 `docs/21-PIPELINE-REPORT.md`；同步 CONTRIBUTING（目录地图/命令/验证流程）、
  README 双语目录树与版本行、docs/16 架构图、`.gitignore`、`setup.ps1` 体检表、CI。

## [1.3.0] - 2026-11-06

### Added
- **QA v4 画风感知边缘检测**（`pipeline/qa/qa_check.py`，`docs/20-QA-V4.md`）：弃用
  `edge_max>235` 绝对亮度线——深底中灰溢出漏检、浅底正常背景全帧误报且暗字溢出完全看不见。
  改为「全片亮度中位数定画风 + 相对背景 ±96 灰阶 + 边带异常面积 ≥0.3%」，深底查亮内容、
  浅底查暗内容；逐帧只缓存 256 级边带直方图（5400 帧约 11MB，零二次读帧）。
- 新增 `--legacy-edge`：单独回退边缘检测（`qa_version=v3`）；`--v2` 保持 v2 全口径回退。
- 报告新增顶层 `edge` 块与 `raw.edge_*` 字段；安全区评分改用 `edge_bleed_count` 全量帧数，
  不再被 `edge_bleed[:10]` 显示截断误导；`review.mjs` 的 QA 汇总卡显示边缘口径与溢出帧数。
- **回归夹具** `pipeline/qa/test_edge_v4.py`：7 条纯合成帧断言（含深底中灰、浅底暗色两个
  历史漏检场景与浅底全帧误报复现），0.3s 跑完，已接入 CI。

### Verified
- 实片同帧对比：demo-hook-compound **8.8 = 8.8**、project-vibe-dsf **9.1 = 9.1**（11 项逐项相同）；
  异常峰值 0.0% / 0.02%，门槛 0.3%，余量 15 倍以上。
- 真实 PNG 端到端注入：30 帧序列第 15 帧左边带贴 deep teal 暗块 → v4 报溢出 @0.47s
  （异常峰值 5.029%、安全区 5/10），`--legacy-edge` / `--v2` 均 0 帧（安全区 10/10）。

### Docs
- 新增 `docs/20-QA-V4.md`；同步 `docs/19`（口径开关表）、`docs/16`（QA 节 / 踩坑表 / 浅底分支）、
  `docs/15`（历史绕过改为根治说明）、`CONTRIBUTING.md`（QA 纪律与命令）、
  `skills/qa-gate/SKILL.md` v1.1.0、`ds-failure-modes.md`（安全区定义）。

## [1.2.0] - 2026-11-06

### Added
- **评审页 QA 联动**（`pipeline/review.mjs`）：自动读 `<project>/qa.json`，页面顶部显示
  QA 总分/过闸状态/qa_version/budgets/最弱三项；场景卡片把静止段、硬切、溢出、
  字幕空档按时间区间标红；静止段中点帧自动补采成**红框病灶帧**（最多 2 张/场景），
  逐帧图注显示时间戳。`--qa <path>` 可手动指定报告，缺 qa.json 时静默降级。
- A/B 模式两侧各自显示 QA 汇总卡（各自找自己的报告）。
- 实测：demo-hook-compound QA 8.82 → 3 处静止标注 + 3 张病灶帧，无头 Chrome 目检通过；
  单片模式与无报告/无帧降级路径均不报错。

## [1.1.0] - 2026-11-06

### Added
- **QA v3 时长缩放口径**（`pipeline/qa/qa_check.py`）：断点/硬切预算按片长缩放——
  `still_budget = max(2, ceil(duration/20))`、`cut_budget = max(6, ceil(duration/15))`；
  180s 长片不再被固定阈值冤枉。短片预算与 v2 完全等价（实测 11.43s 片 8.82→8.82 逐项相同），
  长片 9.18→9.36（断点 8→10）。`--v2` 可回退旧口径做同帧对比，JSON 报告新增
  `qa_version` / `budgets` 字段。
- **版本纪律**：新增 `VERSION` / `CHANGELOG.md`，CONTRIBUTING 写明提交流程，
  CI 加守卫（CHANGELOG 必须含当前版本条目），README 双语显示当前版本。

### Notes
- 静止控制（最长静止段）与片长无关，保持 v2 口径不变。
- 历史 QA 分数均为 v2 口径；v3 起长片分数与历史不可直接横比，用 `--v2` 对齐。

## [1.0.0] - 2026-11-06

企业级公开基线。从"自动化零件、人肉流水线"整理成完整项目。

### Infrastructure
- **结构重组**：`pipeline/` 按职责分 render / qa / audio / compose 四目录，顶层只留
  `run_all.ps1` + `requirements.txt`；`projects/` 8 个实验目录归档 `_archive/`（保留回退）。
- **企业标配**：`.github/workflows/ci.yml`（py/node 语法检查 + `_probe` 夹具冒烟）、
  `CONTRIBUTING.md`（目录地图/加积木流程/QA 纪律/密钥纪律）、`requirements.txt` 补 edge-tts、
  防泄漏审计（env 占位符 + git 全历史无 key）。
- 全库引用同步：run_all 六处、SKILL.md×3、docs×10、README 双语。

### Features（P1 清单全部完成）
- **#5.5 TTS 旁白层**：edge-tts + 窗口拟合 + RMS 侧链闪避（docs/13）。
- **#6 SFX 音效层**：`synth_sfx.py` 六音效白名单、riser 向前铺、SFX 不闪避；
  demo-hook-compound 三层音频首验 QA 8.8 exit 0（docs/17）。
- **#7 品牌契约**：`pipeline/palette.json`，palette_name 引用制 + watermark 回落（docs/18）。
- **#8 强模型分工**：`env-creative.ps1`（云雾 + Claude Opus 5.5）创意帧定调，批量仍走 flash；
  端点迁移实测 v2.cloudmist.cloud（docs/01 §7）。
- **#9 静帧评审页**：`review.mjs` 场景网格 + A/B 按 segment 对齐。
- **#10 缓动库**：`_easings.js` 19 个 GSAP 级缓动，像素一致性 SHA256 实测。

### Content
- 5 条正式样片（QA 8.5–9.5）+ `_probe` 回归夹具；10 积木全过闸入库（registry 分数档案齐）。
- 强调语言改版：数字落定后绝对静止，禁呼吸/伸缩/脉冲（去晃动零代价，QA 不降反升）。
