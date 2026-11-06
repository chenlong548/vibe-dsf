# 18 · 品牌契约（palette.json + 水印）

> P1 #7 交付。解决的问题（G7）：配色和水印散在每条 plan 里手抄——账号没有沉淀成资产。
> 现在一套已验证配色收编进 `pipeline/palette.json`，新片一行 `"palette_name"` 引用全套。

## 一、文件与三层优先级

`pipeline/palette.json` 是账号级品牌契约（与 `blocks/registry.json` 同级的资产文件）：

```jsonc
{
  "brand": { "watermark": "@VIBE·DSF" },     // 账号水印（plan 缺省时自动回落到这里）
  "default_palette": "deep-space",           // plan 什么都没给时用这套
  "palettes": {
    "deep-space": { "style": "...", "pattern": "dots", "bg_in": "...", "accent": "...", ... },
    "paper":      { ... 独立站设计令牌全套 16 键 }
  }
}
```

plan 侧解析优先级（`build_html.mjs` 组装时物化，template 零感知）：

```
内联 meta.palette  >  meta.palette_name（引用库）  >  default_palette
watermark：meta.watermark  >  brand.watermark
```

`palette_name` 引用的是**整套视觉身份**——palette 色键 + `style` + `pattern` 一起生效
（plan 没显式给 style/pattern 时一并回落）。

## 二、当前收录（只收 QA 过闸的）

| 名 | 来源 | QA | 语义 |
|---|---|---|---|
| `deep-space` | demo-hook-entropy / paper-shannon-deep | 9.1 / 9.2 | 深空冷底 + 唯一暖橙，知识片主战场 |
| `paper` | project-vibe-dsf | 9.1 | 独立站设计令牌：暖白纸面 + deep teal + 暗终端证据窗 |

**收编纪律**：新调色先用内联 palette 出片实测，QA 过闸后把整套值（含 style/pattern）
收进 `palettes`，并在 `_from` 字段记出处。库只放验证过的——引用即安全。

## 三、闸的行为（validate_plan.py）

- `meta.palette` 与 `meta.palette_name` **至少给一个**（都不给 → error）
- `palette_name` 不在库里 → error（组装也会拦，双层防线）
- 解析后的配色走同一套 `check_color`：bg_out 禁纯黑、accent 饱和度 s≥0.25 且 v≥0.35、
  accent 不得与 ink/gray 相同
- `meta.watermark` 缺失 → **warning**（不硬卡，组装时自动回落 `brand.watermark`）

## 四、水印

- template 顶栏从 `meta.watermark` 读取渲染（21px、`dim` 基色、字距 4）
- 换账号：只改 `pipeline/palette.json` 的 `brand.watermark` 一处，全部新片生效
- 存量 plan 内联了 watermark 的不受影响（显式值优先）

## 五、新片写法（推荐）

```jsonc
"meta": {
  "topic": "...", "hook_title": "...",
  "duration": 11.43, "fps": 30, "bpm": 126,
  "palette_name": "deep-space"
  // 不写 palette / watermark / style / pattern——全部从品牌契约回落
}
```
