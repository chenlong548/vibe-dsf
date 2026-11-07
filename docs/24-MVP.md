# 24 · MVP 发布面（当前版本功能完整，可直接发布）

> **MVP 在这里是「发布面」的定义，不是功能削减。**
> 当前版本已经能完整跑通「一句话主题 → 可发布成片 + 像素级验收 + 执行报告」。
> 本文只回答三个问题：哪条链路必须稳、怎么一条命令证明它稳、哪些东西保留但不参与验收。
> **仓库里所有现有文件一律保留**（历史归档、额外内容线、风格与技能包都是回退资产），
> 收敛的是心智负担和发布检查面，不是删文件。

## 一、MVP 的一句话

> 给一个主题，产出一条 1080p30 知识视频，附带逐帧 QA 分数与机器可读执行报告；
> 不过 QA 闸就不出片。整条链路本地跑完，不需要 GPU、不需要付费服务、不需要账号。

## 二、必备链路（发布面）

| 阶段 | 文件 | 作用 |
|---|---|---|
| 规划 | `pipeline/scene_writer/PROMPT.md`、`SCENE-PLAN.schema.md` | 主题 → 结构化场景计划 |
| 硬闸 | `pipeline/scene_writer/validate_plan.py` | 11 组检查：拍点、密度、构图重心、字幕不跨场景 |
| 组装 | `pipeline/scene_writer/build_html.mjs` + `blocks/lib/*.js` ×10 | 积木拼成单文件 HTML，`render(t)` 纯时间函数 |
| 渲染 | `pipeline/render/render_frames.mjs` | CDP fast 模式逐帧 1080p PNG，可局部重渲 |
| 门禁 | `pipeline/qa/qa_check.py` | QA v4 十一项评分，`avg < 8 → exit 1` |
| 音频 | `pipeline/audio/`（BGM / SFX / TTS / 闪避混音） | 确定性合成，三层混音 |
| 合成 | `pipeline/compose/build.ps1` | ffmpeg 输出 `final.mp4` |
| 一键 | `pipeline/run_all.ps1` | 串起全部阶段，退出码 0–4 定位失败段 |
| 可观测 | `pipeline/report/generate.py` | 成功与失败都产出 `pipeline_report.json` |
| 夹具 | `projects/_probe/`、`qa/test_edge_v4.py`、`report/test_generate.py` | 无需真实成片的回归基线 |
| 门面 | 双语 README、`site/`、`brand/`、`CHANGELOG.md`、`SECURITY.md` 等 | 对外发布所需 |

`scripts/verify.py` 里的 `CORE_FILES` 是这份清单的机器可读版本，改动此处必须同步那里。

## 三、一条命令验收

```bash
python scripts/verify.py
```

不需要 Chrome、ffmpeg、音频或任何渲染帧；约几秒出结果：

```
=== VIBE-DSF MVP acceptance ===
[PASS] version-sync ...
...
--- 9/9 PASS | MVP READY ---
```

九项检查：`version-sync`（VERSION ↔ CHANGELOG ↔ 双语 README ↔ 站点页脚）、
`core-files`（发布面文件齐全）、`python-syntax`、`node-syntax`、`plan-gate`、
`assemble-smoke`（组装出含 `render()` 的单文件 HTML）、`qa-edge-regression`、
`report-regression`、`site-self-check`。任意一项失败即 `exit 1`，并指出失败项。

**CI 跑的是同一条命令**（`.github/workflows/ci.yml`），本地与远端不会漂移。

### 出片链路的完整验证（需要本机 Chrome / ffmpeg）

```powershell
powershell -File scripts\setup.ps1                 # 环境与文件体检（只读）
powershell -File pipeline\run_all.ps1 -Project projects\demo-hook-compound -SkipRender
```

`exit 0` 且 `pipeline_report.json` 的 `verdict=success`、`pipeline_version` 等于当前 `VERSION`。
全片渲染去掉 `-SkipRender` 并加 `-Duration <秒>`。

### 发布判据

1. `python scripts/verify.py` → 9/9 PASS；
2. 出片链路 `run_all.ps1` → `exit 0`、QA 过闸、`verdict=success`；
3. `VERSION` / `CHANGELOG` / 双语 README / 站点页脚四处版本一致，附注 tag 已推送；
4. 站点 `site/index.html` 可离线打开，EN / 中文切换完整。

完整人工清单见 `docs/23-RELEASE.md`；本文是它的「发布面」前置定义。

## 四、保留但不进发布面（可选扩展，均不阻塞发布）

| 内容 | 位置 | 处理方式 |
|---|---|---|
| 论文→视频线 | `pipeline/paper2video/` | 保留可用，独立内容线，不进 `verify.py` |
| 项目→视频线 | `pipeline/project2video/` | 同上 |
| 静帧评审页 | `pipeline/review.mjs` | 人工挑卡点用，按需调用 |
| Agent 技能包 / 画风规范 | `skills/`、`styles/` | 方法论资产，供创作阶段查阅 |
| 强模型创意帧 | `scripts/env-creative.ps1` | 需自备 Key，缺失不影响主链 |
| 历史方法论文档 | `docs/00–23` | 档案，不作为当前发布门槛 |
| 实验样片归档 | `projects/_archive/` | 保留回退，不清理、不维护 |
| Linux 合成入口 | `pipeline/compose/build.sh` | 跨平台备用 |

判据很简单：**删掉它，`run_all.ps1` 仍能出片、`verify.py` 仍 9/9，它就是可选扩展。**
反过来，动到上表任何一项都不需要走发布门禁。

## 五、明确的边界（不做，也不写成「后续支持」）

- 只做 1920×1080 横屏；竖屏是实测后主动放弃。
- 不引入第二套渲染引擎（Remotion / Motion Canvas / HyperFrames 的结论见 `docs/11`）。
- 无 SaaS、无遥测、无付费连接器、无账号体系；客户只付自己的模型 API 与算力。
- 方法论中部分禁令来自观察而非完整 A/B，文档如实标注，不伪装成实测结论。

后续增强想法统一放在 `docs/25-ROADMAP.md`，**全部是计划项，不进当前验收，也不影响当前版本发布**。
