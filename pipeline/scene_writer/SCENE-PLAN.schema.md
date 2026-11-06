# SCENE-PLAN · 场景规划机器契约 v1.0

> 这是流水线的**规划层契约**。任何 LLM（flash / 强模型 / WorkBuddy 02）按 `PROMPT.md` 产出本格式的 JSON，
> 经 `validate_plan.py` 硬闸校验通过后，由 `build_html.mjs` 组装成单文件 index.html。
> **人不再需要"把每个场景想清楚"——想清楚是任务书 + 校验器的事。**

```jsonc
{
  "version": "1.0",
  "meta": {
    "topic": "复利效应",                    // 一句话主题
    "hook_title": "复利 · COMPOUND",        // 顶栏中央章节标签（全片恒定）
    "duration": 9.524,                     // 秒。必须落在 BPM 拍点网格上
    "fps": 30,                             // 24 | 30 | 60
    "bpm": 126,                            // BGM 拍点网格：beat = 60/bpm
    "style": "deep-space",                 // L0 风格预设（当前支持 deep-space）
    "pattern": "dots",                     // L0 纹理：dots | grid | rings
    "palette_name": "deep-space",          // 推荐：引用 pipeline/palette.json 的已验证配色（一套名=配色+style+pattern）
                                           // 三层优先级：内联 palette > palette_name > default_palette
    "palette": {                           // 内联写法（向后兼容；新调色实测过闸后应收编进 palette.json）
      "bg_in": "#141026",                  // 径向渐变内色（中心比边缘亮 25-40%）
      "bg_out": "#05050F",                 // 外色。禁纯黑（校验器会挂）
      "accent": "#E8A87C",                 // 全片唯一强调色。只染 L2 主角
      "ink":   "#EAEAF2",                  // 主文字
      "gray":  "#8A8AA0"                   // 辅助灰（L3 标注）
    },
    "watermark": "@VIBE·DSF"               // 缺省时 build_html 取品牌契约 brand.watermark
  },

  "scenes": [                              // 时间轴必须无缝全覆盖 [0, duration]
    {
      "id": "S1",
      "segment": "hook",                   // hook|anchor|reason|turn|land（非降序）
      "t_in": 0.0, "t_out": 3.81,          // 边界必须对齐拍点（±0.5 帧）
      "l1": {                              // 可选（data-chart 等积木自带轴）
        "kind": "rings",                   // rings | grid
        "at": [0.42, 0.42],                // 结构中心（归一化），缺省用 l2.cx/cy
        "stroke": 2,                       // ≥2，1px 细线 QA 测不出（实测教训）
        "grow": [0.55, 1.75]               // 生长式进场窗口（绝对秒），禁整层淡入
      },
      "l2": {                              // 必填。一帧一个主角
        "block": "data-chart",             // blocks/registry.json 里注册的积木名
        "params": { "cx": 0.42, "cy": 0.46, "area_pct": 0.16 },
        "glow_window": [0.05, 0.9]         // 可选。全片每场景 ≤1 个发光窗口
      },
      "l3": [                              // dur≥2.5s 的场景 ≥2 条，font 20-26
        { "text": "单利 vs 复利", "x": 0.30, "y": 0.16, "font": 21,
          "align": "center", "color": "gray", "t_in": 1.2, "t_out": null }
      ],
      "beats": [1.905, 3.333],             // 场景内卡点（拍点网格值）
      "sfx":  [ { "t": 3.81, "name": "impact-low" } ]   // name ∈ 白名单
    }
  ],

  "subtitles": [                           // 字幕必须完整落在某个场景内（±0.15s）
    { "zh": "每天进步 1%，一年后会怎样？",
      "en": "Improve 1% a day — what about a year?",
      "t_in": 0.95, "t_out": 3.60,
      "punch": false }                     // punch=true → 进场 0.36s 放大冲击
  ],

  "narration": [                           // 可选。TTS 旁白层（P1-5.5）预留
    { "text": "……", "t_in": 0.95, "t_out": 3.60 }
  ]
}
```

## 校验器强制项（validate_plan.py，违规 exit 1）

| # | 检查 | 阈值/规则 |
|---|---|---|
| 1 | 时间轴守恒 | scenes 无缝无重叠，覆盖 [0, duration] |
| 2 | 拍点对齐 | 场景边界 / beats / sfx.t 全在 60/bpm 网格（±0.5 帧） |
| 3 | L2 主体 | block 已注册；area_pct ≥ 0.12；cx ∈ [0.40,0.46]∪[0.54,0.60] |
| 4 | L1 支撑 | 有则 stroke ≥ 2；grow 窗口在场景内 |
| 5 | L3 标注 | dur≥2.5s 场景 ≥2 条；font 20-26；坐标在画布内 |
| 6 | 密度预算 | est = area_pct + l1(0.05) + l3×0.012 + 纹理(0.02) ≥ 0.12 |
| 7 | 五段叙事 | segment ∈ 枚举且非降序；≥12s 需 ≥3 段；≥20s 需 ≥4 段 |
| 8 | 发光唯一 | 每场景 glow_window ≤ 1 |
| 9 | 配色 | bg_out 禁纯黑；accent 饱和度 s≥0.25 且 v≥0.35 |
| 10 | 字幕 | 不重叠、落在单一场景内、zh 非空；覆盖率 <40% 告警 |
| 11 | 音效 | name ∈ 白名单 {impact-low, impact-mid, tick, riser, sub-drop, whoosh} |

## blocks 注册表（pipeline/blocks/registry.json）

| block | 用途 | 自带 | QA 记录 |
|---|---|---|---|
| `entropy-burst` | 粒子爆发/扩散（钩子爆点） | L2 | 8.5/10 @demo-hook-entropy |
| `data-chart` | 双曲线分叉图表（对比叙事） | L1 轴线 | 待本 demo |
| `beat-counter` | 大数字滚动 + 公式框（锚点/推演） | L2 | 待本 demo |
| `vs-counters` | 左右双数字对撞（落点/转折） | L2 | 待本 demo |

## 使用链路

```
一句话主题
   │  ① 任何 LLM × PROMPT.md
   ▼
SCENE-PLAN.json
   │  ② validate_plan.py（硬闸，违规清单打回重写）
   ▼
过闸规划
   │  ③ build_html.mjs（template + blocks 组装单文件 index.html）
   ▼
projects/<slug>/index.html
   │  ④ run_all.ps1（渲染 → QA 门禁 → 合成）
   ▼
final.mp4（avg≥8 才放行）
```
