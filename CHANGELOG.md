# 更新日志（CHANGELOG）

本项目的版本号为语义化版本（SemVer：MAJOR.MINOR.PATCH）。
**纪律：每一次推送到 GitHub 都递增版本 + 在本文件记录 + 打同名 tag。**
版本判定：新功能/工具增强 → MINOR；修 bug/文档同步 → PATCH；破坏性改动（渲染契约、plan 格式不兼容）→ MAJOR。

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
