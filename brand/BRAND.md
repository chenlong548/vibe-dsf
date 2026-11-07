# VIBE·DSF 品牌规范

> 这一层是**对外包装的单一真相**：站点、README、样片水印、对外材料都从这里取名称与色值。
> 视觉令牌与 `pipeline/palette.json` 的 `deep-space`（QA 9.1 / 9.2 过闸配色）逐项一致，
> 不另造一套色。改动配色必须先过 QA 门禁再入库（见 `docs/18-BRAND.md`）。

## 一、名称

| 场景 | 写法 |
|---|---|
| 产品正式名 | **VIBE·DSF**（中点 U+00B7，全大写） |
| 画面水印 | `@VIBE·DSF`（`palette.json → brand.watermark`） |
| 仓库 / URL / 路径 | `vibe-dsf`（小写连字符，仅作标识符） |
| 禁用 | `VibeDsf`、`VIBE DSF`（缺中点）、把仓库名当产品名 |

## 二、定位与口径

- 中文 tagline：**给个人创作者的知识视频流水线 · 不过 QA 闸不出片**
- English tagline：**A knowledge-video pipeline for solo creators — no QA pass, no film**
- 短标（hero / 分享卡）：**Rendered. Scored. Shipped.**
- **当前 MVP 只服务一类客户**：个人视频制作者 / 起号阶段创作者，只有「免费自托管」一种交付。
  不写机构客户、不写报价档、不写按系列交付。完整产品定义见 `docs/24-MVP.md`。
- 主体口径一律是**团队**：`we` / `our team` / 「我们」。不用个人、学生、接单口径。
  **注意**：「个人创作者」指用户，不是我们；别把服务对象写成自身定位。
- 面向海外的材料只讲 Web / CLI / 桌面工具形态，不引入国内平台专有概念。
- 不承诺分数：QA 数字只对应具体样片，写成「实测 8.8–9.5」，不写「保证 9 分」。
- 站点页脚不写死版本号；版本只由 `VERSION` / `CHANGELOG.md` / README 双语维护。

## 三、配色（deep-space）

| 令牌 | 色值 | 用途 |
|---|---|---|
| `bg_in` | `#141026` | 渐变内圈 |
| `bg_out` | `#05050F` | 渐变外圈 / 页底 |
| `accent` | `#E8A87C` | **唯一强调色**：CTA、焦点、下划线、光带 |
| `ink` | `#EAEAF2` | 主文字 / 字标 |
| `gray` | `#8A8AA0` | 次级文字 / 分隔线 |
| `dim` | `138,138,160` | `rgba()` 透明底用 |

`paper` 皮肤（`accent #0d6e63`）只用于**项目介绍片**的内容画面，不是主品牌色；
品牌资产一律使用 deep-space。

## 四、字体与数字

- 英文：`Inter, "Helvetica Neue", Arial, sans-serif`（站点不外链字体，离线可开）
- 中文：`"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`
- 数字：`font-variant-numeric: tabular-nums`，**落定后绝对静止**——禁呼吸、伸缩、脉冲、
  alpha 闪烁；强调靠一次性下划线扫出，运动感交给巡游光带 / 粒子流（见 `docs/05`）。
- 入场淡入 ≤0.2s；`prefers-reduced-motion` 下停止全部环境动效。

## 五、资产清单

| 文件 | 用途 | 最小尺寸 |
|---|---|---|
| `brand/logo.svg` | 主标（深底、透明背景） | 字标高度 ≥20px |
| `brand/favicon.svg` | 站点图标 / 头像 | ≥24px |
| `site/og-card.svg` | 社交分享卡（1200×630） | 原尺寸使用 |
| `docs/demo.gif` | README 首屏动图 | 宽度 ≤800px |

mark 四周留白 ≥0.25×mark 宽度。深底版 logo **不可直接放浅底**；需要浅底版时另出反色资产，
不要临时改 `fill` 凑合。

## 六、禁用示例

- 改强调色、加第二个强调色、渐变文字、投影、拉伸变形、旋转字标
- 把「VIBE·DSF」拆成两行或改变字母间距
- 在数字上做循环动画（与全项目的「去晃动」纪律冲突）
- 把样片 QA 分数当成服务 SLA 写在对外材料里
- 把冻结档案（旧方法论、额外画风、归档样片）包装成当前对外承诺
