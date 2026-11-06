# 14 · PAPER2VIDEO：论文 → 科普视频（两步拆解 + 既有流水线）

> 解决什么：把"一篇论文"翻译成"一条过闸的科普视频"。翻译本身也自动化——
> 论文是论证结构，视频是叙事结构，中间隔着**两层机器约束的翻译**：
> ① 论文 → PAPER-BRIEF（讲什么，人可 10 秒审阅）② PAPER-BRIEF → SCENE-PLAN（怎么画/念/卡点）。
> 后半程（积木组装/渲染/QA 门禁/旁白/BGM/合成）全部复用既有流水线，零新增。

---

## 一、全链路

```
论文 PDF ──(paper_text.py 提取文本)
              │
              ▼  ① PROMPT-EXTRACT.md（拆解任务书 × 任何 LLM）
        PAPER-BRIEF.json ──(validate_brief.py 闸：钩子≥2/机制3-5步/数字全溯源/防误读≥1)
              │
              ▼  ② PROMPT-SCRIPT.md + scene_writer/PROMPT.md（规划任务书）
        SCENE-PLAN.json ──(validate_plan.py 闸：拍点/密度/构图/字幕)
              │
              ▼  ③ build_html.mjs（blocks 组装）
        index.html ──(渲染 → QA 门禁 ≥8 → run_all.ps1：旁白+BGM+混音+合成)
              │
              ▼
        final.mp4（1080p30 + 人声 + -14 LUFS）
```

## 二、两层任务书各管什么

| 层 | 文件 | 产出 | 关键约束 |
|---|---|---|---|
| 拆解 | `PROMPT-EXTRACT.md` | PAPER-BRIEF.json | 只翻译不发挥（数字必须带 source）、钩子必须反常识、机制链说人话、类比标失效点 |
| 规划 | `PROMPT-SCRIPT.md` | SCENE-PLAN.json | 数字只从 brief 取、类比贴防误读标签、论文出处进 l3、旁白按"读法音节"估窗、narration 与 subtitles 可不同文 |

**人审点**：brief 是唯一事实源——选题对不对、数字准不准，看完 brief 再放行进规划。

## 三、诚实纪律（科普的命根子，逐条过）

1. 每个上片数字能在 brief.numbers 里指到 `source`（章节/图表定位）
2. 统计口径进画面：如"4.7 bit/字母"必须带"按字符统计 · 一阶近似"标注
3. brief.caveats 最狠的一条给 turn 段——防误读本身就是转折段的素材
4. land 金句只到 one_liner 为止，不声称论文没证明的东西

## 四、首条论文片实测（Shannon 1948）

`projects/paper-shannon1948/`：五段完整 23.81s（50 拍 @126BPM），6 句旁白。

- 双闸：brief 一次过；plan 一次过（≥20s 的 ≥4 段叙事校验首次实战）
- **QA 迭代 8.1 → 9.5**，暴露并消灭了"数字/曲线类积木密度低"的通病，三板斧全部沉淀进库：
  1. **模板级萤火虫层**：500 个 3-5px 粒子（accent/ink 各半，alpha 0.22-0.55，每粒子独立 8-14 rad/s 快闪）——帧差 >8 阈值的本质是"每帧亮度差要够"，快闪让整块矩形计入变化像素
  2. **data-chart 回流粒子加亮**（alpha ≤0.75，ω=6）
  3. **整数计数器改 decimals=1**（"0.0→1.0" 每帧滚动）+ 定格呼吸脉冲 2%→3.5%
- 旁白：6 句全 natural/轻拟合（tempo 1.0-1.11）零截断——"读法音节 × 4.5 音节/秒"估窗法实战验证
- 验收：714 帧 QA 9.5 过闸、ffprobe 双流（1080p30 + aac 44.1k）、关键帧目检（曲线粒子/对撞/标注）

## 五、长视频章节化（120-180s 深讲版）

短片（≤24s）是把一个钩子讲完；深讲片是把钩子的"为什么"展开成章节。**五段骨架不变**（非降序纪律照卡），变化全在 reason 段——它从一个场景膨胀为**章节场景组**。

**时间骨架**
- 时长先对齐拍网格：126BPM 下 180.0s = 378 拍整，所有场景边界落在整拍上（validate_plan 的拍点 ±0.5 帧照卡）
- reason 段每章一个独立场景：12-25s、禁 >26s（超过就再拆章），一个积木讲一件事
- hook / anchor / turn / land 保持短片的节奏密度（5-10s 级），不动

**章节纪律（已写进 PROMPT-SCRIPT）**
1. 章节开头要有"定位感"——上一章收尾即本章起手，观众任何时候都知道讲到哪了
2. 同一积木全片 ≤3 次、相邻场景不同积木（防视觉疲劳）
3. land 段画面回声 hook（同积木、同构图重心），首尾闭环
4. 旁白 24-30+ 句，句间 0.15-0.3s 气口，句窗仍按"读法音节 × 4.5 音节/秒"估
5. BGM 卡点喂场景边界 + 章节内爆点（run_all.ps1 -BgmMarks）

**实测 paper-shannon-deep（180.0s / 378 拍）**
- brief：机制 7 步（工程接力进机制链）、数字 4 组（0.5 冗余比等）、caveats 4 条（存在性证明最狠给 turn）
- plan：10 场景 = 1 hook + 1 anchor + 6 reason 章节 + 1 turn + 1 land；31 字幕、32 句旁白；双闸一次过
- 新积木 3 个：flow-pipe（管道接力）/ text-points（要点点亮）/ timeline（年代轴）
- 旁白 32 句：28 natural + 4 tempo（最高 1.131，远低于 1.25 警戒）零截断零警告
- BGM 20 卡点；混音峰值 -2.4 dBFS、闪避覆盖 56.4%（长片旁白只占一半时长，句间呼吸是特性不是缺陷）
- QA：**9.2/10 过闸**（三轮：8.1 → 8.3 → 9.2。关键治理=给"曲线/要点类"积木补大面积持续
  运动源——细线下划线凑不够 0.35%/帧变化底线，巡游光带才是解；静止控制 4→10，断点 5→8）
- 渲染：5400 帧 fast 模式净渲染 ~75 min（0.82s/帧，长 HTML + 7 积木全开负载，单帧比 24s 片慢数倍——长片预算要按 5 倍估）

## 六、命令速查（论文片全流程）

```bash
python pipeline/paper2video/paper_text.py paper.pdf paper.txt --max-chars 12000
# ① 喂 PROMPT-EXTRACT.md + paper.txt 给 LLM → PAPER-BRIEF.json
python pipeline/paper2video/validate_brief.py projects/<slug>/PAPER-BRIEF.json
# ② 喂 PROMPT-SCRIPT.md + scene_writer/PROMPT.md + brief 给 LLM → SCENE-PLAN.json
python pipeline/scene_writer/validate_plan.py projects/<slug>/SCENE-PLAN.json
node pipeline/scene_writer/build_html.mjs --plan projects/<slug>/SCENE-PLAN.json --out projects/<slug>/index.html
cd projects/<slug> && node ../../pipeline/render_frames.mjs --duration <秒> --fps 30
python ../../pipeline/qa_check.py frames/ --fps 30
# ③ 声音链 + 合成（一键）：
powershell -File ..\..\pipeline\run_all.ps1 -SkipRender -Duration <秒> -BgmStyle vibe -Bpm 126 -BgmMarks "<切点秒值,逗号分隔>"
```

## 七、后续

- ~~长视频版（深讲 2-4 分钟）~~ ✅ 2026-11-06 落地（见第五节）
- 系列化：一篇论文一条 hook 片 + 一条深讲片，同 brief 复用
- 拆解层扩展：输入不止论文——技术文档/书籍章节/公众号长文同构适用（PROMPT-EXTRACT 不用改）
