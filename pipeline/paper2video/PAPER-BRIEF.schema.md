# PAPER-BRIEF · 论文拆解契约 v1.0

> 论文 → 视频翻译层的中间产物。由 `PROMPT-EXTRACT.md` 产出，`validate_brief.py` 校验，
> `PROMPT-SCRIPT.md` 消费（→ SCENE-PLAN.json → 现有流水线）。
> **人审点**：brief 是"这条片讲什么"的唯一事实源——10 秒读完就能判断选题对不对。

```jsonc
{
  "version": "1.0",
  "meta": {
    "title": "A Mathematical Theory of Communication",   // 论文原题
    "authors": "Claude E. Shannon",
    "year": 1948,
    "field": "信息论 / 通信",                             // 领域标签
    "one_liner": "香农把'信息'变成了可计算的量——万物皆可比特化",   // 一句人话结论
    "audience": "对计算机技术感兴趣的普通观众",
    "duration_target": 23.8095,                           // 秒，须对齐拍点（见 SCENE-PLAN 校验）
    "bpm": 126
  },

  "hook_candidates": [                                    // ≥2 条，按冲击力排序
    { "claim": "今天所有数字通信的地基，是一篇诞生时无人问津的论文",
      "why_it_works": "反常识：奠基之作当年默默无闻", "strength": 5 },
    { "claim": "信息可以被'称重'——单位是比特",
      "why_it_works": "反常识：抽象概念有度量衡", "strength": 4 }
  ],

  "mechanism": [                                          // 因果链 3-5 步，每步人话
    { "step": 1, "say": "通信就是把一条消息从 A 搬到 B，不关心意思",
      "visual": "两点一线 + 消息粒子流动" },
    { "step": 2, "say": "信息的量 = 消灭不确定性需要的最少'是否问题'数",
      "visual": "抛硬币 / 猜谜分支树" }
  ],

  "numbers": [                                            // ≥2 条，全部带 source + comparison
    { "value": 4.7, "unit": "bit/字母",
      "claim": "按字符统计，一段英文平均只带 4.7 比特",
      "comparison": "抛一次硬币的答案 = 1 bit",
      "source": "论文 Part 3 对英文统计熵的估计（一阶近似）" }
  ],

  "metaphors": [                                          // 类比素材，每条标失效点
    { "concept": "熵 = 意外程度", "everyday": "越猜不到的事，说出来信息越多",
      "breaks": "熵不衡量'有没有用'——废话连篇也可以高熵" }
  ],

  "quote": {                                              // 论文金句（可做字幕/落点）
    "en": "The fundamental problem of communication is that of reproducing at one point, either exactly or approximately, a message selected at another point.",
    "zh": "通信的根本问题，是把一点选择的消息在另一点精确或近似地重现。",
    "where": "论文第一句（Part 1 引言）"
  },

  "caveats": [                                            // ≥1 条防误读边界
    "4.7 bit/字母是香农 1948 年的一阶统计估计；计入上下文冗余的现代估计约 1.5 bit/字母",
    "香农信息熵 ≠ 语义信息：不衡量内容的价值或真假"
  ]
}
```

## validate_brief.py 强制项

| # | 检查 | 规则 |
|---|---|---|
| 1 | meta 必填 | title/authors/year/one_liner/audience/duration_target |
| 2 | 钩子数量 | hook_candidates ≥ 2，每条 claim+why_it_works 非空 |
| 3 | 因果链 | mechanism 3-5 步，每步 say 非空 |
| 4 | 数字溯源 | numbers ≥ 2，每条 value/unit/claim/comparison/source 四件套齐全 |
| 5 | 防误读 | caveats ≥ 1；metaphors 有 breaks 的比例 ≥ 50% |
| 6 | 时长 | duration_target 为正（拍点对齐由 SCENE-PLAN 校验器把关） |

## 链路位置

```
论文全文 ──(PROMPT-EXTRACT)──▶ PAPER-BRIEF.json ──(validate_brief 闸)
                                              │
                                              ▼
                            SCENE-PLAN.json ──(PROMPT-SCRIPT + scene_writer/PROMPT.md)
                                              │
                                              ▼
                              validate_plan 闸 → build_html → 渲染 → QA → 旁白 → 成片
```
