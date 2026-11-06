# 模型画像：DeepSeek-V4.1-Flash-1017（`deepseek-flash`）

> 数据来源：[DeepSeek 官方价目表](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)（2026-10 抓取）。
> **本文只描述 flash。**这套生态不为其他模型留分支，理由见 `00-INVENTORY.md` 第二节。

## 1. 硬指标

| 项 | 值 | 对视频意味着什么 |
|---|---|---|
| 实际版本 | DeepSeek-V4.1-Flash-1017 | — |
| 上下文 | **1M** | 整片代码 + 风格包 + 分镜表 + QA 报告全塞得下，中途不用"翻回去看" |
| 最大输出 | **384K** | **一次吐 3000–4000 行单文件**，不用分块拼接 → 变量名不漂移、坐标不重复 |
| 思考模式 | 默认开启，可切非思考 | **保持开启**：分镜和坐标计算需要推理，关掉明显变笨 |
| 图像理解 | **支持** | "渲帧 → 看图 → 改码"闭环成立（本生态的核心机制） |
| 工具能力 | JSON / Tool Calls / Responses API / Anthropic API / FIM / 前缀续写 | Anthropic API 兼容 → `SKILL.md` 生态可直接借用 |
| 并发上限 | **2500** | 多项目并行、批量抽卡都不受限 |

## 2. 价格（人民币 / 百万 token）

| | 缓存命中 | 缓存未命中 | 输出 |
|---|---|---|---|
| **空闲时段** | ¥0.02 | ¥1 | ¥4 |
| **高峰时段** | ¥0.04 | ¥2 | ¥8 |

- **空闲 = 高峰的一半。** 高峰只有工作日 9:00–12:00、14:00–18:00；其余时间（含周末、法定节假日全天）全按空闲价。
- **缓存命中 ¥0.02/M** 是本生态设计的支点：风格包 + 10 条禁令**全文常驻上下文**，每轮成本约 ¥0.001。
- Search / Fetch：¥5 / 千次；2026-11-01 起 Harness 内调用开始计费（此前免费）。

## 3. 一条片多少钱

| 片长 | 空闲 | 高峰 |
|---|---|---|
| 30 秒样片 | ¥0.8 | ¥1.6 |
| 60 秒 | ¥1.5–2.5 | ¥3–5 |
| 120 秒 | ¥3–5 | ¥6–10 |

口径：常规档，约 400k 输出 / 2M 输入 / 85% 缓存命中。

## 4. 参数怎么配

| 参数 | 任务 | 取值 | 理由 |
|---|---|---|---|
| 温度 | 写代码 | **0.3** | 要稳 |
| 温度 | 改文案 | 0.7 | 保留句式只换词 |
| 温度 | 选题 / 分镜创意 | **0.9** | flash 创意是短板，靠高温抽卡 |
| 思考 | 全部 | **开** | 关掉会明显变笨 |
| 输出上限 | 全部 | **≥32K** | 单文件 2000 行，默认值会截断 |
| 一次写多少 | 首稿 | **整片一次写完** | 384K 输出就是给你这么用的 |
| 一次改多少 | 改稿 | **一个场景函数 / 一个常量** | 防止整文件重写癖 |

## 5. 环境变量（全部锁到 flash）

```powershell
$env:ANTHROPIC_BASE_URL   = "https://api.deepseek.com/anthropic"
$env:ANTHROPIC_AUTH_TOKEN = "<你的 Key>"
$env:ANTHROPIC_MODEL      = "deepseek-flash[1m]"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL   = "deepseek-flash[1m]"   # 关键：把 opus 也锁成 flash
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "deepseek-flash[1m]"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL  = "deepseek-flash"
$env:CLAUDE_CODE_SUBAGENT_MODEL     = "deepseek-flash"
$env:CLAUDE_CODE_EFFORT_LEVEL       = "max"
$env:CLAUDE_CODE_AUTO_COMPACT_WINDOW = "786432"
```

**为什么把 `opus` 也锁成 flash**：默认映射是 `claude-opus*` → v4-pro。你在 Claude Code 里若触发到 opus 档，会**悄悄换模型**，风格和习惯全变。锁死它。

现成的脚本：`scripts/env.ps1`。

## 6. 已知短板（必须在流程里补偿）

| 短板 | 表现 | 补偿 |
|---|---|---|
| 审美偏"安全" | 居中、对称、等距、均匀分布 | `ds-failure-modes.md` 的 F1/F3 禁令 |
| 整文件重写癖 | 改 1 个字吐 2000 行 | 强制最小 diff + 自报改了哪几行 |
| 自我评价失真 | 说"挺好的"，实际有溢出 | `qa_check.py`，数字优先 |
| 长上下文会记混 | 忘记禁令、坐标串场景 | 60% 上下文换会话（playbook 第 8 条） |
| 多任务会互相污染 | 一个回合改三处，坏两处 | 一次一件事（playbook 第 7 条） |
| 创意密度低 | "正确但无聊" | 温度 0.9 出 5 个方案挑 1 |

## 7. 模型分工（P1 #8）：创意帧给 Opus，批量给 flash

flash 的创意密度是结构性短板（第 6 节第一条）——禁令和模板只能保底，拔不高上限。
强模型分工不是换模型，是**按任务性质路由**：

| 任务 | 模型 | 环境 | 为什么 |
|---|---|---|---|
| 风格定义 / 首版创意帧抽卡 | **Opus 5.5** | `scripts\env-creative.ps1`（云雾） | 审美方差大=优点，一次出高密度构图；每片只做 1-2 次 |
| 复杂积木首版（entropy-burst 类） | **Opus 5.5** | 同上 | 首版质量决定积木上限，入库后 flash 直接复用 |
| 批量场景帧 / 局部修补 / QA 修复循环 | flash | `scripts\env.ps1` | ¥3-5/片；1M 上下文吃任务书；禁令可 grep |
| plan 编写（SCENE-PLAN.json） | flash | 同上 | 闸会拦错——机器校验面前模型便宜优先 |
| 规划闸 / 组装 / 渲染 / QA / 混音 | **无模型** | 管线代码 | 已全部机器化，不烧 token |

**成本直觉**：Opus 5.5 是 $4/$20 每百万 token（输入/输出，约为 flash 的 10-20 倍），
但创意帧环节每片只跑 1-2 次（几千 token 级），摊到一条片不到 ¥0.5——
**用 2% 的成本买定调质量，批量环节一分不涨**。

**Opus 5.5 行为注意**：自适应思考常开（不可关），effort 档 low/medium/high/xhigh/max
控制深度；Creative 会话默认 `CLAUDE_CODE_EFFORT_LEVEL=max`。

**云雾接入（2026-11 实测）**：旧 `yunwu.ai` / `api.yunwu.cloud` 已停用迁移——
新注册用户用 `https://v2.cloudmist.cloud`，老用户用 `https://api.cloudmist.cloud`
（两站 Key 不通用）。Claude Code 的 `ANTHROPIC_BASE_URL` 不带 `/v1`。
模型 ID：`claude-opus-5-5`（1M ctx / 128K 输出）。填充 key 后自测：
`curl -s --noproxy "*" -X POST https://v2.cloudmist.cloud/v1/messages -H "Authorization: Bearer sk-你的key" -H "Content-Type: application/json" -d "{\"model\":\"claude-opus-5-5\",\"max_tokens\":8,\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}]}"`
