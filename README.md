<div align="center">

<img src="brand/logo.svg" width="420" alt="VIBE·DSF — knowledge video pipeline"/>

**给个人创作者的知识视频流水线 · 不过 QA 闸不出片**

[展示站点](site/index.html) · [English](README.en.md) · **v1.7.0** · [更新日志](CHANGELOG.md) · [MVP 定义](docs/24-MVP.md) · [升级计划](docs/25-ROADMAP.md) · [对外定位](docs/22-COMMERCIAL.md)

`免费 · MIT` · `QA ≥ 8 硬门禁` · `零付费依赖` · `自托管`

</div>

---

# VIBE·DSF

> 我们把一句话主题变成可发布的 1080p 知识视频：画面由代码绘制，音频确定性合成，
> 逐帧渲染后由**像素级 QA 门禁**验收——不过线不放行。

**这一版只服务个人视频制作者 / 起号阶段创作者**：一个人做选题、出片、发布，没有
剪辑、设计、工程同事可依赖，也没第二双眼睛把关。我们把「把关」交给可测的数字。
输入源与片长都有（一句话 / 论文 PDF / 仓库 README，8–180s），但只有一条主链；
开源免费、本机跑完，不需要团队、服务器或付费服务。完整产品定义见
[docs/24-MVP.md](docs/24-MVP.md)。

## 一、为什么这么做

| 痛点 | 我们的做法 |
|---|---|
| 模型自评不可信（「挺好的」，其实字幕被裁了） | 11 项像素级 QA，`avg < 8 → exit 1` 硬卡流水线 |
| 画面密度靠感觉，成片忽好忽坏 | 把审美翻译成可测指标：纹理能量 / 构图重心 / 强调色 / 字幕占用 |
| 改一帧要重出整片 | `render(t)` 是纯时间函数，同帧 SHA256 一致，支持按秒局部重渲 |
| 长片没人知道卡在哪一步 | 每次运行产出 `pipeline_report.json`：阶段耗时、产物清单、失败阶段 |

## 二、能力一览（均为实测能力）

| 能力 | 实现 | 实测 |
|---|---|---|
| 逐帧渲染 | `pipeline/render/render_frames.mjs`（CDP fast 模式） | 0.65 → **0.13s/帧**（4.9×），1080p30 |
| 质量门禁 | `pipeline/qa/qa_check.py`（QA v4） | 11 项评分，画风感知安全区，avg≥8 放行 |
| 音频 | BGM + 六音效白名单 + edge-tts 旁白 + RMS 侧链闪避 | 三层混音，−14 LUFS 合成 |
| 内容生成线 | 主题 / 论文 PDF / 仓库 README → `SCENE-PLAN.json` | 三条线共用 100% 后半程 |
| 组件库 | `pipeline/blocks/` 10 个积木 + `registry.json` 分数档案 | 全部过闸入库 |
| 品牌契约 | `pipeline/palette.json`（palette_name 引用制） | 只收 QA 过闸配色 |
| 人工评审 | `pipeline/review.mjs` | 场景网格 / A/B 对比 / QA 病灶叠加 |
| 执行报告 | `pipeline/report/generate.py` | 成功与失败路径都产出，事件流 append-only |
| 回归保障 | `test_edge_v4.py` + `test_generate.py` + `_probe` | CI 自动跑，15 条断言 |

## 三、架构

```
主题一句话 / 论文 PDF / GitHub 仓库
   ↓  BRIEF 契约 + 校验闸
SCENE-PLAN.json ──(validate_plan.py 11 组硬闸)──→ build_html.mjs
   ↓  10 个积木组装成单文件 HTML
render_frames.mjs ──(CDP 逐帧)──→ frames/*.png
   ↓
qa_check.py ──(11 项 / avg≥8 硬门禁，未过线即停)──→ qa.json
   ↓
BGM + SFX + TTS ──(mix_audio.py 闪避混音)──→ build.ps1 (ffmpeg) ──→ final.mp4
   ↓
generate.py ──→ pipeline_report.json ／ review.mjs ──→ 人工挑卡点
```

`pipeline/run_all.ps1` 把上述阶段一键串联（渲染 → QA 闸 → BGM → 音效/旁白 → 混音 → 合成 → 报告），
退出码 `0 / 1 / 2 / 3 / 4` 分别定位到具体失败段。

## 四、目录结构

```
brand/                 主标 / 图标 / 品牌规范（BRAND.md）
site/                  可发布双语展示页 index.html + og-card.svg + check.py
pipeline/
├── run_all.ps1        一键流水线（每次产出执行报告）
├── review.mjs         静帧评审页
├── palette.json       品牌契约 · requirements.txt
├── render/            CDP 逐帧渲染
├── qa/                11 项门禁 + 边缘回归夹具
├── report/            阶段事件 → pipeline_report.json + 回归夹具
├── audio/             BGM / 音效 / 波形；narrate/ 为 TTS 与闪避混音
├── compose/           ffmpeg 合成（build.ps1 / build.sh）
├── blocks/            10 个积木 + registry.json
├── scene_writer/      主题 → SCENE-PLAN（任务书 / 硬闸 / 组装器）
├── paper2video/       论文 → PAPER-BRIEF → SCENE-PLAN
└── project2video/     仓库 → PROJECT-BRIEF → SCENE-PLAN
projects/              5 条正式样片 + _probe 回归夹具 + _archive 历史归档
skills/ styles/ docs/ scripts/ .github/
docs/                  活跃：22 对外定位 / 23 发布清单 / 24 MVP 定义 / 25 升级计划；00–21 冻结档案
```

完整目录地图、依赖方向与加积木流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 五、跑起来（MVP 三步）

**只想确认这一版能不能跑**——三步，前两步不需要 Chrome / ffmpeg：

```bash
python scripts/verify.py                 # 1) 全项 PASS 即 MVP READY
```

```powershell
powershell -File scripts\setup.ps1       # 2) 环境与文件体检（只读）
powershell -File pipeline\run_all.ps1 -Project projects\demo-hook-compound -SkipRender
                                       # 3) 出片：QA 闸 + 音频 + 合成 + 执行报告
```

`run_all.ps1` 去掉 `-SkipRender` 并加 `-Duration <秒>` 即全片渲染；
成功后看 `pipeline_report.json`。产品定义见 [docs/24-MVP.md](docs/24-MVP.md)，
后续增强都是不阻塞发布的计划项，见 [docs/25-ROADMAP.md](docs/25-ROADMAP.md)。

依赖：Python 3.10+（`numpy` / `pillow` / `edge-tts`）、Node 20+、本机 Chrome、ffmpeg。
不需要 GPU，也不需要付费连接器。

<details>
<summary>分步命令（需要手动控制某个阶段时）</summary>

```powershell
# 在项目目录里：分步跑 / 局部重渲
node ..\..\pipeline\render\render_frames.mjs --fps 30 --duration 8
python ..\..\pipeline\qa\qa_check.py frames --fps 30 --json qa.json
python ..\..\pipeline\audio\synth_bgm.py bgm.wav --bpm 77 --duration 8
powershell -File ..\..\pipeline\compose\build.ps1 -Audio bgm.wav
node ..\..\pipeline\render\render_frames.mjs --start 3 --end 5

# 在仓库根目录：人工评审（场景网格 / A/B 对比 / QA 病灶叠加）
node pipeline\review.mjs --project projects\demo-hook-compound
```

</details>

站点是单文件静态页，双击 `site/index.html` 即可离线打开；`python site/check.py` 是发布自检。

## 六、质量与可观测性

- **QA v4**：安全区按片子自身画风判定（深底查亮内容溢出、浅底查暗内容溢出），
  取代旧版绝对亮度线的双盲；`--v2` / `--legacy-edge` 可回退做同帧对比（`docs/20`）。
- **执行报告**：阶段耗时、QA 摘要、8 类产物字节数、`verdict` 与 `failed_stage`；
  QA 拦截时同样落盘（`docs/21`）。
- **CI 与本地同源**：CI 只跑 `python scripts/verify.py`（版本同步、活跃面文件、
  语法、规划硬闸、组装冒烟、两个回归夹具、站点自检），本地与远端不会漂移；
  冻结档案不进检查，新增积木 / 文档 / 样片不需要登记。
- **诚实边界**：只做 1920×1080 横屏；方法论中的部分禁令来自观察、未全部做 A/B；
  竖屏是实测后主动放弃，不写成「后续支持」。

## 七、样片

<img src="docs/demo.gif" width="720" alt="demo-hook-entropy · 8s 自动生成的知识视频片段"/>

| 样片 | 内容线 | 片长 | QA |
|---|---|---|---|
| demo-hook-entropy | 四层构图基线片 | 8s | 9.1 |
| demo-hook-compound | SCENE-WRITER 全自动 + 旁白 + 音效 | 11.43s | 8.8 |
| paper-shannon1948 | PAPER2VIDEO 论文科普 | 23.81s | 9.5 |
| paper-shannon-deep | PAPER2VIDEO 章节化长片 | 180s | 9.2 |
| project-vibe-dsf | PROJECT2VIDEO 项目自举片 | 50s | 9.1 |

五条都在**同一条主链**上，只是输入源与片长不同（8–180s）——不是五条产品线。
分数来自各片实际渲染帧的 `qa.json`（短片在 v2/v3/v4 口径下逐项等价）。
帧、音频与成片都是本地可重建产物，不入库。

## 八、给谁用 · 怎么拿到

**只服务个人视频制作者 / 起号阶段创作者**，只有一种交付方式：

| | |
|---|---|
| 得到 | 完整开源仓库（MIT），本机跑完，无账号、无遥测、无服务器 |
| 花费 | ¥0；无订阅费、无 token 加价，只可能花自己的模型 API 用量与算力 |
| 定制 | 有具体需求可在 Issues / Discussions 提，不设报价档、不排期、不承诺交付 |

Integration / Managed series / 发现会报价这类 B2B 档位已从对外材料移除 ——
它们对个人创作者不成立。详见 [docs/22-COMMERCIAL.md](docs/22-COMMERCIAL.md)。

## 九、文档地图（活跃 / 冻结分层）

**活跃维护面**（随版本同步、进 CI、保证可跑）：README 双语、
[docs/22](docs/22-COMMERCIAL.md) 对外定位、[docs/24](docs/24-MVP.md) MVP 定义、
[docs/23](docs/23-RELEASE.md) 发布清单、`site/`、一条主链与 `scripts/verify.py`。

**冻结档案**（留仓库可回退，不进对外承诺、不进 CI、不随版本同步）：

| 编号 | 主题 |
|---|---|
| 00–09 | 配齐清单、模型画像、flash 方法论、风格 DNA、失败模式、构图模板 |
| 10–11 | 差距分析、引擎选型结论 |
| 12–15 | SCENE-WRITER / 旁白 / PAPER2VIDEO / PROJECT2VIDEO 三条内容线的额外契约 |
| 16–21 | 全景总结、SFX、品牌契约、QA v3 / v4、执行报告 |
| 25 | 后续升级计划（计划项，不进验收、不阻塞发布） |

文件一个都不删；冻结档案随时可重新激活，激活前先评估维护成本（`docs/24` 第六节）。

## 十、合规与维护

- 自建部分 [MIT](LICENSE)，上游风格数值按各自许可（见 LICENSE 尾段）。
- [SECURITY.md](SECURITY.md)：漏洞披露、密钥纪律、本地运行无遥测、依赖清单。
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)：社区准则。
- 每次推送 GitHub 递增 `VERSION` + 更新 `CHANGELOG.md` + 打同名 tag，CI 有守卫；
  完整发布清单见 [docs/23-RELEASE.md](docs/23-RELEASE.md)。

## 参考来源

- [DeepSeek 官方价目表](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) · [Claude Code 接入 DeepSeek](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code)
- [vibe-knowledge-video](https://github.com/xiazhuo123456789/vibe-knowledge-video)（风格数值来源） · [vibe-knowledge-film](https://github.com/HeyChengC/vibe-knowledge-film)
- [DSH 插件库](https://dsh.yeyupiaoling.cn/)（本项目主动不采用，理由见 `docs/00-INVENTORY.md`）
