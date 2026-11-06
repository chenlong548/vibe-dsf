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
| `data-chart` | 双曲线分叉（自带轴+巡游光带） | hook, anchor, reason | 9.5/10 @ paper-shannon1948 |
| `beat-counter` | 大数字滚动 + 公式框 | anchor, reason | 9.5/10 @ paper-shannon1948 |
| `vs-counters` | 双数字对撞（右侧胜出） | turn, land | 9.5/10 @ paper-shannon1948 |
| `flow-pipe` | 节点链管道（通信模型/流程） | anchor, reason | 9.2/10 @ paper-shannon-deep |
| `text-points` | 要点逐条点亮（下划线+巡游光带） | reason, anchor | 9.2/10 @ paper-shannon-deep |
| `timeline` | 年份轴（扫掠游标+呼吸环） | anchor, turn, land | 9.2/10 @ paper-shannon-deep |
| `feature-cards` | 编辑部式特性卡（白卡+teal 顶条+巡游光带） | anchor, reason | 8.5/10 @ project-vibe-dsf |
| `terminal-window` | 终端证据窗（暗面板+逐字敲入+扫描带+进度条） | reason, turn | 8.5/10 @ project-vibe-dsf |
| `repo-card` | 收尾卡（owner/name+星数+安装命令呼吸描边） | land | 8.5/10 @ project-vibe-dsf |

> **运动源铁律（2026-11-06 QA 实测沉淀）**：1080p30 下静止判定线 = 每帧变化像素 ≥0.35%
> （~7.2k px，|亮度差|>8）。3px 细线/微脉冲**没有面积**，怎么动都凑不够；长场景必须配
> **大面积匀速平移的光带**（110px 宽、两缘 ~10px/帧 ≈ 9.7k px/帧）或粒子流。
> 另：入场淡入 >0.4s 时，一次淡入会被计成连续多次"硬切"（面板 ≈25% 画幅）——入场统一 ≤0.2s。
>
> **强调语言（2026-11-06 用户定调）**：**数字/圆点/标记落定后绝对静止——禁止呼吸、伸缩、
> 脉冲、alpha 闪烁**（scale 呼吸看着别扭）。强调 = 落定瞬间下方 accent 下划线**一次性扫出**
> （easeOutCubic ~0.6s，落定后静态保持）；持续运动感一律交给场景级巡游光带/粒子流，
> 主体元素永远稳。终端光标闪烁是终端本命语言，保留。

> **缓动纪律（P1 #10，`lib/_easings.js`）**：GSAP 级全集 19 个挂在 `EASE` 命名空间
> （build_html 恒定注入，积木直接用）。规则：easeOutBack 是阻尼版定稿值（与历史像素一致），
> 只准用于一次性入场/扫出；**禁 Elastic/Spring 类振荡缓动**（落定后晃动=强调语言红线，
> 库里故意不提供）；新积木优先用 EASE.* 而不是自写闭式曲线。

params 语义详见 `registry.json`。QA 结果过闸后由人工/02 更新本表与 registry（把 pending 换成分数）。

## 新增积木流程

1. 从某条过闸成片提炼代码 → `lib/<name>.js`（去掉剧情特判，参数化窗口时间）
2. 本地 QA 过闸 → registry.json 登记（含 params 文档 + QA 记录 + 待替换分数）
3. scene_writer 的 PROMPT.md「积木选型」表同步加一行
