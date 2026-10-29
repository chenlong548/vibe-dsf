# 11 · AI 视频框架全景调研（2026-10）

> 调研问题：*"感觉我们自研的质量不够，看到了 Remotion / HyperFrames 啥的"* ——
> 换引擎能不能解决质量问题？结论先行：**不能。引擎不是瓶颈，架构上 HyperFrames 和我们是同一条路。**
> 真正的缺口在「内容密度 + 音效 + 配音」三层，全部与渲染引擎无关。

---

## 一、全景四象限

| 象限 | 代表 | 与本流水线的关系 |
|---|---|---|
| ① 程序化动效引擎 | Remotion / Motion Canvas / HyperFrames / Manim | **直接竞品/同类**，逐帧渲染 HTML/代码 |
| ② AI 生成模型 | Sora 2 / Veo 3.1 / Kling 3.0 / Seedance 2.5 / Wan | 不同赛道（实拍感镜头），可做 B-roll 插片，非主力 |
| ③ 配音层（TTS） | CosyVoice / Fish Audio / GPT-SoVITS / F5-TTS | **我们缺失的层**，比特新语有我们无 |
| ④ 音效/后期自动化 | ffmpeg / loudnorm / 自研 synth_* | 已有雏形，P1 继续补 |

---

## 二、程序化引擎逐个评估

### Remotion（React 视频框架）
- React 组件 → 逐帧渲染，Lambda 云渲染（60s/1080p：本地 2m15s vs 云 18s）
- 免费额度：年收入 <$1M 免费；周下载 6 万，社区最大
- **AI agent 适配最好**（官方 docs 就面向 agent 编写）
- ✗ 范式是 React 组件树 —— 采用=全量重写；Lambda 云渲染在我们日产量（个位数视频）下无意义

### Motion Canvas（程序化 TS 生成器）
- 生成器函数式写动画 + 内置编辑器，MIT
- ✗ **核心仓库 2024-12 起沉寂**，社区转向 fork（Revideo / Canvas Commons）—— 引入即背债

### HyperFrames（HeyGen，2026-04 开源）★ 最值得关注
- 工作流：AI agent 写 HTML+CSS+JS+**GSAP 时间线** → `npx hyperframes render` → **无头 Chrome 逐帧 + ffmpeg 合成**
- 配套：registry blocks（apple-money-count、data-chart、code-typing 等成品组件）、KeyFrames 关键帧库、agent skills（`npx skills add heygen-com/hyperframes`）、透明通道 WebM/MOV 输出
- 定位：**<10s（上限约 30s）短动效**，已并入 HeyGen Video Agent
- **关键事实：它的渲染路径与我们自研管线完全同构**（HTML→无头 Chrome 截帧→ffmpeg）。换成它，画面质量上限一分不加。

### Manim
- 数学教育专用，3Blue1Brown 赛道；我们的知识叙事风格用不上

### 对照表：自研 vs 三框架

| 维度 | 自研 render(t) | Remotion | Motion Canvas | HyperFrames |
|---|---|---|---|---|
| 渲染路径 | HTML→无头 Chrome→ffmpeg | 同左（Chrome headless） | Chrome 截帧 | **同左，同构** |
| 确定性渲染 | ✅ t 参数纯函数 | ✅ | ✅ | ✅（GSAP 时间线） |
| agent 产出友好 | ✅ 单文件 HTML，flash 直接写 | 需理解 React 组件 | 需理解生成器协议 | 需理解 GSAP 时间线 |
| QA 门禁 | ✅ **独有**，11 指标 exit 1 | ✗ | ✗ | ✗ |
| 组件库 | ✗（靠 layer-templates 手搓） | 生态大 | 小 | ✅ registry blocks |
| 云渲染 | ✗（不需要） | ✅ Lambda | ✗ | HeyGen 云 |
| 采用成本 | 0 | 全量重写 | 全量重写 | 中（引 GSAP+改产出协议） |

> README「零插件」决策（拒掉 dsh-hyperframes/dsh-remotion，防 flash 混淆）经本次调研**维持有效**。

---

## 三、AI 生成模型（象限②）—— 不换赛道，但记一笔

2026 年格局（关键事实）：
- **Sora 2 已死**：Web/App 2026-04-26 停服，API 2026-09-24 终止（成本过高 + SAG-AFTRA 诉讼）—— 单一订阅制时代结束
- **中国模型性价比碾压**：Kling 3.0 / Seedance 2.5 平均 $0.04/秒（抖音/快手数据飞轮），物理动态领先
- **Veo 3.1**：电影级画质 + 原生立体声，8s 镜头内最强；美区锁定
- **Kling 3.0**：4K@60fps、Motion Brush、业界最强文字保留、5 国语言口型；$0.084-0.168/秒
- **Seedance 2.5**：50 个多模态参考、30s 原生单镜（四强最长）、音画联合生成
- **「思考模式」进视频模型**：Wan 2.7 / Seedream 5.0 先用 LLM 编排分镜再生成帧 —— 与我们 CUE-SHEET 先行的方法论同向，算旁证

对知识区动效视频的意义：
- 比特新语风格 = **动效图形 + 配音 + 音效**，不是 AI 实拍镜头 → 换赛道无意义
- 唯一值得留的口子：**钩子段 8s B-roll 插片**（Kling 8s ≈ ¥0.5-1），P2 再议，不引入新依赖

---

## 四、配音层（象限③）—— 本次调研挖出的最大缺口

比特新语每条视频有旁白驱动节奏，我们管线目前**零人声**。开源可选：

| 方案 | GitHub | 克隆样本 | 特点 | 协议 |
|---|---|---|---|---|
| **CosyVoice**（阿里） | 13.7k | **3 秒** | 细粒度情感指令（哭腔/方言）、流式 150ms、声调最稳 | Apache 2.0 |
| **GPT-SoVITS** | **56k** | 5 秒 | 情绪继承参考音频最好、社区最大；RTF 0.5-1 偏慢 | MIT |
| **Fish Audio** | 17k | 10-30 秒 | 唯一「在线 API+免费额度+13 语言」；成本 ≈ ElevenLabs 1/6；48kHz WAV | Apache 2.0 |
| **F5-TTS** | 12k | **2 秒** | RTF 0.15 最快、呼吸感最像真人；偶有吞声母 | MIT |
| ElevenLabs | — | 1 分钟 | 英文天花板；**中文韵律差**、国内不可直连 | 商业 |

选型判据（对齐本流水线约束）：
- **本地免费无限**（需 N 卡 ≥8G 显存）→ CosyVoice（首选，情感控制最利于知识叙事）或 GPT-SoVITS
- **无 GPU/免部署** → Fish Audio API（免费额度 + SRT 分段贴文本即可逐句合成）
- 英文出海内容才考虑 ElevenLabs

---

## 五、核心论证：为什么引擎不是瓶颈

1. **同构证据**：HyperFrames = HTML+GSAP → 无头 Chrome 逐帧 → ffmpeg。与我们 render(t) → CDP 截帧 → ffmpeg 完全同构，不存在「它的渲染质量更高」这回事。
2. **自家 QA 数据**：同一个引擎，film-love-math 内容密度不足得 7.14，demo-hook-entropy 按四层模板重做得 **8.5**。差距 100% 来自设计纪律，0% 来自渲染器。
3. **调研结论旁证**：横向评测原话 —— *"visual quality depends more on design choices than the rendering engine"*。
4. **独有优势**：QA v2 十一指标硬门禁，四个框架都没有。换引擎=扔掉差异化资产。

---

## 六、行动结论

### 不做
- ✗ 换 Remotion（全量重写，质量零增益，Lambda 我们用不上）
- ✗ 换 Motion Canvas（上游沉寂）
- ✗ 整体迁移 HyperFrames（同构 + 零插件决策维持）

### 偷思想（低成本移植进自研）
- ① **组件注册表**：学 registry blocks，把 layer-templates 落成 `pipeline/blocks/` 可复用组件库（数据图表、计数器、代码打字机……每个过 QA 才入库）
- ② **缓动预设库**：GSAP 级 easing 曲线整理成 `easings.js`，render(t) 直接引用（弹性/回弹/指数进出）

### 补真缺口（P1 优先级据此刷新）
- ③ **TTS 旁白层**（新增，优先级高于原 P1 #6）：CosyVoice 本地 or Fish Audio API，先做 film-love-math 旁白版 A/B
- ④ 音效轨 synth_sfx.py（原 P1 #6，与 TTS 同属「听觉层」一起补）
- ⑤ 品牌契约 palette.json（原 #7）、强模型创意帧（原 #8）、静帧评审页（原 #9）

### 观察哨
- Remotion：若频道起量（日产 >10 条）再评估 Lambda 云渲染
- Kling 3.0 B-roll：钩子段实拍感插片，P2
- HyperFrames：关注其 registry blocks 更新，好组件的思想持续吸收

---

*调研执行：2026-10-29，检索源：most.tw / pixmind / seavidgen / searchingc / 51CTO / hqwc / qishijinka / cnblogs + Remotion/Motion Canvas/HyperFrames 官方渠道汇总*
