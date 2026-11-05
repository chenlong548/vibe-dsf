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

## 五、命令速查（论文片全流程）

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

## 六、后续

- 长视频版（60-90s 深讲）：机制链 4 步全展开 + 信道容量定理，需要新积木（管道容量/分支树）
- 系列化：一篇论文一条 hook 片 + 一条深讲片，同 brief 复用
- 拆解层扩展：输入不止论文——技术文档/书籍章节/公众号长文同构适用（PROMPT-EXTRACT 不用改）
