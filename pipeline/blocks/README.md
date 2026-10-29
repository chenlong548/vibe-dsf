# blocks · 场景积木库

> 学 HyperFrames registry blocks 的思想，落在自研 render(t) 契约上：
> **规划 = 选积木 + 填参数，不 = 从零发明画面。** 每个积木都是提炼自过 QA 成片的代码段。

## 铁律

1. **过 QA 才入库**：新积木必须先在某条成片里跑出 QA avg≥8，才允许登记进 registry.json。
2. **确定性**：所有随机性由 params.seed 派生；禁止 Date.now()/Math.random()；禁止跨帧可变状态
   （预计算数组只读缓存允许）。
3. **契约**：每个积木实现 `l2(ctx, T, sc, P, U)`（可选 `l1`）。`T`=绝对秒，`P`=场景 params，
   `U`=模板工具集（见下）。窗口时间一律用绝对秒，由规划层给出。
4. **强调色纪律**：积木只允许给 L2 主角染 `U.ACCENT`；全片每场景发光 ≤1 个。

## U 工具集（template.html 注入）

| 成员 | 说明 |
|---|---|
| `W, H` | 1920 / 1080 |
| `ACCENT / INK / GRAY` | 调色板三色（来自 PLAN.meta.palette） |
| `rgba(a)` / `rgbaInk(a)` | 强调色 / 主文字色的 rgba 字符串 |
| `seg(t,a,b)` / `clamp01` / `easeOutCubic` / `easeOutBack` | 时间窗与缓动 |
| `drawText(ctx, text, x, y, opt)` | 折行文字（px 解析用正则，防 NaN 静默不画） |

## 注册表

| block | 用途 | 适用段位 | QA 记录 |
|---|---|---|---|
| `entropy-burst` | 粒子爆发/能量释放 | hook, turn | 8.5/10 @ demo-hook-entropy |
| `data-chart` | 双曲线分叉（自带轴） | hook, anchor, reason | 9.1/10 @ demo-hook-compound |
| `beat-counter` | 大数字滚动 + 公式框 | anchor, reason | 9.1/10 @ demo-hook-compound |
| `vs-counters` | 双数字对撞（右侧胜出） | turn, land | 9.1/10 @ demo-hook-compound |

params 语义详见 `registry.json`。QA 结果过闸后由人工/02 更新本表与 registry（把 pending 换成分数）。

## 新增积木流程

1. 从某条过闸成片提炼代码 → `lib/<name>.js`（去掉剧情特判，参数化窗口时间）
2. 本地 QA 过闸 → registry.json 登记（含 params 文档 + QA 记录 + 待替换分数）
3. scene_writer 的 PROMPT.md「积木选型」表同步加一行
