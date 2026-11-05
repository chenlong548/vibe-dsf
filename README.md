# vibe-dsf · 只服务 flash 的视频生态

> **唯一目标模型：DeepSeek-V4.1-Flash-1017（`deepseek-flash`）**
> 不提供 v4-pro 分支、不做双模型对比、不装为别的模型准备的插件。
> 每一个设计决策的理由都是"因为 flash 是这样"。

```
选题 → facts.md → script.md → storyboard.md → 2 版静帧 → 30 秒样片 → 全片
                                                              ↓
                          qa_check.py（像素级验收）← 逐帧渲染 ← index.html
                                                              ↓
                                                    synth_bgm.py + ffmpeg → final.mp4
```

---

## 一、这份生态只吃 flash 的四个特性

| flash 的特性 | 这条路怎么用它 | 对应文件 |
|---|---|---|
| **384K 输出**（同类里最大） | 2000–3000 行单文件**一次写全**，之后只 patch 那几行 | `03-FLASH-PLAYBOOK.md` 第 1 条 |
| **1M 上下文 + 缓存 ¥0.02/M** | 风格包 + 10 条禁令**全文常驻**，成本可忽略 | 第 2 条 |
| **图像理解** | "渲帧 → 看图 → 改码"闭环，一次最多看 3 张 | 第 3 条 |
| **方差大、成本低** | 静帧出 2 版抽卡；失败原样重跑而不是改提示词 | 第 4、5、12 条 |

**反过来说，这三件事它是短板，所以生态里全是补偿：**

| 短板 | 补偿机制 | 在哪 |
|---|---|---|
| 审美偏"安全"（爱居中/对称/等距） | 把审美翻译成 **10 条可 grep 的硬禁令** | `skills/vibe-film-ds/references/ds-failure-modes.md` |
| 倾向整文件重写（改 1 字吐 2000 行） | 强制最小 diff + 每轮自报改了哪几行 | `SKILL.md` 第 5 步、playbook 第 10 条 |
| 自我评价失真（"挺好的"，其实字被截了） | **像素级验收器，数字说了算** | `pipeline/qa_check.py` |

---

## 二、插件：一个都不装（明确答复）

这是结论，不是"可选"：

| 插件 | 它做什么 | 装不装 | 理由 |
|---|---|---|---|
| `dsh-hyperframes` | HyperFrames 五件套（自带渲染器 + GSAP） | **不装** | 会引入**第二条渲染路径**。flash 最典型的失误就是在两套 API 之间横跳（一会儿 `render(t)`、一会儿 HyperFrames 的 `data-start`），结果是渲染出半截片。本生态只有一条渲染链 |
| `dsh-remotion` | React 组件式视频 + 38 条规则 | **不装** | 需要 React 工具链，且 38 条规则讲的是 Remotion API，与我们的单文件 Canvas **零重叠**。纯增上下文负担 |
| `dsh-ffmpeg` | 7 类 ffmpeg 工具 | **不装** | `build.ps1` + `render_frames.mjs` 已覆盖抽帧/合成/转码。多一条命令 = 多一个出错面，而且它输出的参数不受我们的响度规范约束 |
| `modlens` | 给**纯文本模型**补视觉 | **不装** | **flash 自带图像理解**，装它纯属冗余 |

**唯一会让你想装的理由**：想偷懒少写 shell。但代价是——当 agent 有两条路可走时，flash 会走错的那条，而且它不会告诉你。

> 如果哪天你**真的**要做 3D 或 React 视频，再来装 `dsh-remotion`；
> 但那是另一个项目，不是这套。

---

## 三、目录结构

```
vibe-dsf/
├── README.md                    ← 你正在看的（定位 + 决策 + 用法）
├── docs/
│   ├── 00-INVENTORY.md          配齐清单：6 个能力域 + 零插件决策表
│   ├── 01-MODEL-PROFILE.md      flash 画像：硬指标、价格、参数
│   ├── 02-FLASH-EDGE.md         用闪存换迭代：为什么这个组合反而更强
│   ├── 03-FLASH-PLAYBOOK.md     ★ 12 条 flash 专用调优
│   └── 04-AB-RESULT.md          ★ 对照实验：禁令把 7.7 拉到 9.1（含局限声明）
├── skills/
│   ├── vibe-film-ds/SKILL.md    主技能：7 步 + 回看回路
│   │   └── references/
│   │       ├── style-dna.md           数值规范（照抄）
│   │       └── ds-failure-modes.md    ★ 10 条硬禁令（自建）
│   ├── qa-gate/SKILL.md         验收技能
│   └── bgm-synth/SKILL.md       配乐技能
├── styles/                     画风包（横屏）
│   ├── paper-gold.md            ✅ 已出片（哲学/社科/诺奖故事）
│   ├── nocturne.md              ✅ 已出帧（物理/数学/算法）
│   ├── romance.md               ✅ 已出帧（爱情/亲情/怀念）
│   └── fable.md                 ⬜ 仅竖屏版，横屏待改（心理/行为）
├── pipeline/                   模型无关的五件套（已实测）
│   ├── render_frames.mjs        逐帧抓图（CDP 快模式 0.13s/帧 / 只重渲某段）
│   ├── qa_check.py              像素级验收 v2（11 指标，avg≥8 硬门禁）
│   ├── synth_bgm.py             确定性 BGM（ambient 纪录片 / vibe 电子两种风格）
│   ├── wave_png.py              把 wav 画成波形图（agent 听不见，只能看图验）
│   ├── build.ps1 / build.sh     ffmpeg 合成（−14 LUFS）
│   ├── run_all.ps1              一键流水线：渲染→QA 闸→BGM→合成
│   ├── scene_writer/            ★ 场景规划自动化：PROMPT 任务书 + validate_plan 硬闸 + build_html 组装
│   ├── blocks/                  ★ 场景积木库（过 QA 才入库）：entropy-burst / data-chart / beat-counter / vs-counters
│   ├── narrate/                 ★ 旁白层：edge-tts 合成 + 窗口对齐 + BGM 闪避混音（docs/13）
│   ├── paper2video/             ★ 论文→视频翻译层：拆解任务书 + brief 闸 + 规划衔接（docs/14）
│   └── requirements.txt
├── projects/
│   ├── demo-26s/               ★ 已出片样片（纸金风，26 秒 1080p30）
│   ├── demo-hook-entropy/      ★ 熵增 8s 钩子（四层构图验证片，QA 8.5）
│   ├── demo-hook-compound/     ★ 复利 11.4s 钩子（SCENE-WRITER 全自动 + 人声旁白，QA 8.8 过闸）
│   ├── paper-shannon1948/      ★ 香农 1948 论文科普 23.8s（PAPER2VIDEO 全自动，QA 9.5 过闸）
│   ├── nocturne-demo/          深空理性验证帧（8 秒）
│   └── ab-test/                A/B 对照实验（同镜头两种写法）
└── scripts/
    ├── setup.ps1               体检（不动系统）
    └── env.ps1                 环境变量（全部锁到 flash）
```

---

## 四、配齐状态

| 能力域 | 状态 | 实现 |
|---|---|---|
| 画面（代码渲染） | ✅ | `projects/demo-26s/index.html`，780 帧已渲完 |
| 声音（BGM） | ✅ | `synth_bgm.py`，已生成 `bgm.wav` |
| 渲染（抓帧+合成） | ✅ | 780 帧 / 并发 8 / 实测推算 7–8 分钟（后台跑过 24 分钟的先例，见 playbook 第 11 条） |
| 验收（质量门禁） | ✅ | `qa_check.py` 实测 9.4 与 8.3 分 |
| 风格（画风包） | ✅ 2 套已出片 | 纸金 `paper-gold`（26s 成片）、理性 `nocturne`（验证帧）；`fable` 仅竖屏版（横屏待改） |
| 事实（选题核实） | ✅ | DeepSeek Search/Fetch（¥5/千次） |
| **审美对照实验** | ✅ 已做 | A 默认 7.7 / B 按禁令 **9.1**，见 `docs/04-AB-RESULT.md` |
| 插件 | ⛔ 不装 | 见第二节，这是决策不是缺口 |
| 配音 TTS | ⬜ 未做 | 无旁白路线已够用；要口播需接第三方 |

体检实测：**16 项通过 / 0 缺失**（`powershell -File scripts\setup.ps1`）。

### 验证状态（哪些是真测过，哪些只是写下来）

| 项 | 状态 | 证据 |
|---|---|---|
| 确定性渲染（同 t 同像素） | ✅ 已验证 | 两次抓帧 PNG SHA256 一致 |
| 780 帧 → MP4 | ✅ 已验证 | 跑通过两次，26.00s / 1080p30 / h264+aac / bt709 |
| `qa_check.py` | ✅ 已验证并校准 | 首版阈值把我自己的 demo 判成 6.7 分不合格，按实测重定后 9.4 / 8.3 |
| `synth_bgm.py` | ✅ 已验证 | 26.00s wav，mean −21.3dB / peak −4.4dB |
| `setup.ps1` / `build.ps1` | ✅ 已验证 | 16/16 通过；`exit 0`、bt709、BOM 都已修 |
| **并发对速度的影响** | ⚠️ 已验证且**推翻原假设** | 4/8/12 都是 0.54–0.57 s/帧，±5%（详见 playbook 第 11 条） |
| **竖屏 1080×1920** | ⛔ 放弃（决策） | 2026-10-22 决定**只做横屏**。实测过：传宽高只会得到上下黑边，需重写坐标系统，不值得 |
| `nocturne` 画风 | ✅ 已出帧 | `projects/nocturne-demo/`：坐标轴生长 + 收敛曲线 + 标准误参数卡 |
| `romance` 画风 | ✅ 已出帧 | `projects/romance-demo/`：落日暖调 + 散景 + 纸条手写（爱情片验证） |
| `fable` 画风 | ❌ **仅竖屏版，横屏待改** | 原始规范是竖屏的，本项目只做横屏，所以它还没被改成横屏（不是"不支持竖屏"） |
| **A/B 对照实验** | ✅ 已做（非盲测） | 同一镜头两种写法：7.7 → 9.1；但 B 的密度 0.21% 仍低于 0.3% 线 |
| 10 条失败模式 | ⚠️ 观察假设 | 来自我自己的输出习惯，没做对照实验 |
| 12 条调优 | ⚠️ 半验证 | 第 11 条已修正；其余是流程约定，未逐条量化 |
| 插件 | ⛔ 主动拒绝 | 从未安装，也无计划 |

**一句话：工程链路我全测过，方法论我大部分没测。**

---

## 五、跑起来

```powershell
# 0) 体检（只读，不动系统）
powershell -File scripts\setup.ps1

# 1) 看样片
cd projects\demo-26s
start final.mp4

# 2) 改一个变量，出自己的帧（出 2 版抽卡）
node ..\..\pipeline\render_frames.mjs --stills 3,45,132

# 3) 全片 + 验收 + 合成
node ..\..\pipeline\render_frames.mjs --fps 30 --duration 26
python ..\..\pipeline\qa_check.py frames --fps 30 --json qa.json
python ..\..\pipeline\synth_bgm.py bgm.wav --bpm 77 --duration 26
powershell -File ..\..\pipeline\build.ps1 -Audio bgm.wav

# 4) 只重渲某几秒（改文案后最常用）
node ..\..\pipeline\render_frames.mjs --start 41 --end 47
```

---

## 六、成本（只有 flash 一列）

| | 空闲时段 | 高峰时段 |
|---|---|---|
| 2 分钟片 | **¥3–5** | ¥6–10 |
| 60 秒片 | ¥1.5–2.5 | ¥3–5 |
| 30 秒 A/B 样片 | ¥0.8 | ¥1.6 |

空闲 = 工作日 9–12 / 14–18 之外**全部时间**（含周末、节假日）。**把"写代码 + 看图"排在晚上，直接省一半。**

---

## 七、下一步

**最快出片路径（SCENE-WRITER，2026-10-29 起）**：给一句话主题 + 时长，走
`docs/12-SCENE-WRITER.md` 的四步链路——规划、校验、组装、渲染全部自动，
成片不过 QA 门禁不放行。人工只做两件事：给主题、看成片。

整片定制（7 步全流程）依旧可用：**领域 / 观众要记住的一句话 / 选哪套画风**
（纸金 或 深空理性 —— 只做横屏 1920×1080，画幅不用选）。

我会按 7 步走，每步停下来给你确认；每条片跑完把 **token 账** 打在最后，让你看清钱花在哪。

---

## 八、参考来源

- [DeepSeek 官方价目表](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) · [Claude Code 接入 DeepSeek](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code)
- [vibe-knowledge-video](https://github.com/xiazhuo123456789/vibe-knowledge-video)（风格数值来源） · [vibe-knowledge-film](https://github.com/HeyChengC/vibe-knowledge-film)
- [DSH 插件库](https://dsh.yeyupiaoling.cn/)（14499 个插件，本生态**一个都不用**，理由见第二节）

自建部分 MIT。上游风格数值请遵守其许可。
