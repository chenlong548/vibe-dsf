# PROMPT · 规划衔接任务书（PAPER-BRIEF → SCENE-PLAN）

> **给谁用**：任何 LLM。喂给它三样东西：本文件 + `pipeline/scene_writer/PROMPT.md` + 过闸的 PAPER-BRIEF.json。
> **解决什么**：brief 是"讲什么"，SCENE-PLAN 是"怎么画、怎么念、卡什么点"。
> 本任务书只写**论文科普的特化规则**，通用硬约束（拍点/密度/构图/字幕）全部沿用 scene_writer/PROMPT.md。

---

## 输出

一个完整的 SCENE-PLAN.json（契约 `pipeline/scene_writer/SCENE-PLAN.schema.md`），
外加 `meta.topic` 填论文主题词、`meta.hook_title` 填"论文名缩写 · 年份"。

## 论文科普特化规则（在通用硬约束之上叠加）

### 叙事映射（brief → 五段）

| 段位 | 装什么 | 取自 brief |
|---|---|---|
| hook | 反常识钩子，字幕=问句或惊句 | hook_candidates[0].claim 改写成口语 |
| anchor | 论文金句或第一个数字锚 | numbers[0] 或 quote |
| reason | 机制链展开（1-2 个场景） | mechanism 步骤 + numbers[1..] |
| turn | 防误读/认知反转/历史反差 | caveats[0] 或论文命运的反常识 |
| land | one_liner 收口成金句 | meta.one_liner + quote |

### 诚实纪律（科普的命根子）

1. **数字只从 brief.numbers 取**——每个上片的数字必须能在 brief 里指到 source。
   SCENE-PLAN 的 l3 标注要写单位与口径（如"按字符统计"）。
2. **类比必须贴"防误读"标签**：画面用 metaphor 时，该场景的 l3 或字幕要带限定词
   （"类比""按字符统计""不含语义"），brief.caveats 里最狠的一条要给 turn 段。
3. **结论只到 one_liner 为止**：land 金句可以修辞，不能声称论文没证明的东西。
4. **年份/人名进画面**：l3 至少一处论文出处（作者 · 年份 · 原题缩写），专业感 + 溯源。

### 旁白口语化（TTS 念出来的）

1. **句子按"读法音节"估长**：数字念全称（1948→"一九四八" 4 音节；4.7→"四点七" 3 音节；
   365→"三百六十五" 5 音节）。经验值：+15% 语速 ≈ 4.5 音节/秒，窗口留 10% 余量。
2. **书面语→口语转写**："研究表明"→"他们发现"；"该模型"→"这个模型"；被动改主动。
3. **数字句优先拆句卡点**：设问在动画进行时，揭晓在数字命中拍上（beat-counter 的 t_count 终点）。
4. **narration 与 subtitles 可以不同文**：narration 是嘴说的（可拆句），subtitles 是屏显的
   （完整句、不跨场景）。两者语义一致，措辞不必逐字相同。

### 积木选型直觉（对应论文叙事件）

| 论文里有什么 | 用什么积木 |
|---|---|
| 分布/趋势/增长/对比曲线 | `data-chart` |
| 单位/度量/里程碑数字 | `beat-counter` |
| 新旧对撞/前后反差/两个数 | `vs-counters` |
| 爆发/扩散/不确定性能量 | `entropy-burst` |

同一论文片全流程：`validate_plan.py`（拍点/密度闸）→ `build_html.mjs` → `render_frames` →
`qa_check`（画面闸）→ `run_all.ps1`（旁白+BGM+合成，自动）。

## 输出格式

只输出一个 JSON 代码块（SCENE-PLAN.json 全文）。被 validate_plan.py 打回时只修违规项。
