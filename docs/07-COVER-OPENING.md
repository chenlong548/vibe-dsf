# 封面 / 片头规范（开头的 3–5 秒）

> 来源：开源提示词里的两个片头类作品
> - [3D Logo Intro Animation Studio](https://github.com/yihui-dev/awesome-opus5-5-videos/blob/main/prompts/juancarlos17626-429530.md)（@juancarlos17626）
>   原文提炼：**"碎片飞入 → 组装 → 旋转 → 一道闪光扫过 → 名字逐字出现"**
> - [Opus 5.5 Brand Teaser](https://github.com/yihui-dev/awesome-opus5-5-videos/blob/main/prompts/utsavchopra30-560359.md)（@UtsavChopra30）：先扫全站元素与品牌信息，再出**高端 teaser**
>
> 两条共同的骨架：**先给"零件"，再给"成品"，中间用一个瞬间事件（闪光/冲击）连接。**

## 一、四拍结构（4 秒版）

| 拍 | 时间 | 动作 | 参数 |
|---|---|---|---|
| **1 飞入** | 0.00–1.10 | 10–14 个碎片从画面外不同方向飞入，带旋转 | `easeOutBack`，位移 600–900px，旋转 20–40°，逐个错开 0.05s |
| **2 组装** | 1.10–1.90 | 碎片收拢成"框"或一个符号，整体过冲再回弹 | 缩放 1.0→1.06→1.0，`easeOutBack`，回弹幅度 ≤6% |
| **3 闪光** | 1.90–2.55 | 一道窄光带横扫（左→右），同时画面亮度抬 20% | 光带宽度 180px，速度 2600px/s，0.35s 走完 |
| **4 亮字** | 2.55–4.00 | 标题逐字出现（每字 60ms），副标跟上，最后一下放大冲击 | 字距 +6%，字号 ≥ 下图；冲击 1.0→1.10 |

**收尾**：最后 0.15s 压暗 30%，硬切进正片。**不要在片头里淡出到全黑**——那会让正片的开场显得断档。

## 二、视觉约束（与正片一致）

- 机位固定（跟正片同一套规则），动的是碎片和字
- 只用一个强调色；片头比正片**亮 15%**（观众刚进入，需要抓眼）
- 背景沿用正片最后一章的色调 → 形成"封面→正片"的色调衔接
- 全片强调点预算里，片头占 **2 个**（闪光 + 标题冲击），正片留 3–6 个

## 三、工程上怎么做（整合进工作流）

**独立文件，独立渲染，编码时拼接**——不写进正片的 `render(t)`：

```
cover.html          DUR=4      →  120 帧  →  cover_frames/
index.html          DUR=180    →  5400 帧 →  frames/
ffmpeg concat      cover_frames + frames → final.mp4
```

理由：
1. 片头要换标题/换季时，**不用重渲正片**
2. 片头可以给别的视频复用（把标题当参数传进去）
3. 计时的错误只影响 4 秒，不会污染正片的时间轴

**命令**（已封装在 `projects/_archive/film-love-math/`）：
```powershell
node ..\..\pipeline\render\render_frames.mjs --html cover.html --duration 4 --start 0 --end 4 --out cover_frames
node ..\..\pipeline\render\render_frames.mjs --duration 180 --out frames
# 合成时先拼帧目录，再走 build.ps1
```

## 四、检验清单

| 项 | 判据 |
|---|---|
| 0.5 秒内有没有东西在动 | 有碎片已经进画 |
| 有没有"瞬间事件" | 必须有闪光/冲击之一 |
| 标题能不能在 1 秒内读完 | 主标题 ≤ 10 字 |
| 与正片衔接是否顺 | 片头结束的色调 = 正片开场的色调 |
| 总长 | 3–5 秒，超过 5 秒会吃掉完播率 |
