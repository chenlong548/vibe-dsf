# PROMPT · 项目拆解任务书（GitHub 项目 → PROJECT-BRIEF）

> **给谁用**：任何 LLM。喂给它两样东西：本文件 + 项目的 README 文本（可附仓库元信息：stars/语言/文件树/示例输出）。
> **解决什么**：把"一个 GitHub 项目"翻译成"一条项目介绍视频的事实源"。
> 产出 PROJECT-BRIEF.json 是唯一事实源——后续分镜、画面、旁白只从这里取数。
> 人审点：看完 brief 30 秒内能判断"介绍得准不准、吹没吹"。

---

## 输出

一个 JSON 文件（契约见 `PROJECT-BRIEF.schema.md`）。

## 拆解纪律（项目片和论文片不同：怕的不是"讲错理论"，是"吹牛"）

1. **只翻译不发挥**：每个 feature 的 what 必须能在 README 里指到原文依据；
   README 没写的能力不许上片。
2. **证据先行**：features[].proof 必填——数字、命令、真实输出、文件路径都算证据，
   "很强大""非常好用"不算。README 里连证据都找不到的特性，不值得上片。
3. **钩子来自反差**：项目钩子最好的素材是"旧做法成本 vs 新做法成本"
   （3 天 vs 30 分钟、500 行配置 vs 一行命令）。pain.old_way_cost 就是给这个用的。
4. **limits 是防吹牛闸**：≥1 条项目边界（"不支持 X""目前只验证过 Y"）。
   介绍片的可信度来自敢说做不到什么。
5. **数字全溯源**：metrics[].source 写清楚（"README 性能小节""repo 首页 badge"）。
   stars 这种会过期的数字要标注统计时间。
6. **说人话**：what/claim 面向没读过 README 的人；术语第一次出现给口语解释。

## 字段速览

| 字段 | 要求 |
|---|---|
| meta.one_liner | ≤32 字：它是什么 + 给谁 + 核心价值 |
| pain | 谁的什么痛 + 旧做法成本（钩子素材） |
| hook_candidates | ≥2 条，每条 ≤32 字反差句 + why_it_works |
| features | 3-6 条，每条 name(≤8字) + what(≤32字人话) + **proof(必填)** |
| quickstart | install 命令 1-3 条 + first_output 真实输出摘录 + time_to_demo |
| metrics | ≥1 条四元组（value/unit/claim/comparison/source） |
| limits | ≥1 条项目边界（防吹牛） |
| cta | repo_url + 一行安装命令 |

## 自查（输出前逐条过）

- [ ] 每个 feature 的 proof 我能在 README 原文里指到
- [ ] one_liner 里没有"最""第一""革命性"这类没证据的词
- [ ] metrics 的 source 写了具体位置；stars 标了统计时间
- [ ] limits 至少 1 条，且不是凑数的客套话
- [ ] quickstart 的命令和输出是 README/实测原文，不是我猜的
