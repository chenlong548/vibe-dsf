# 16 · 项目全景总结（2026-11-06）

> 一句话：**自动化知识视频流水线**——一句话主题 / 一篇论文 / 一个 GitHub 仓库进去，
> 过硬性质量门禁（QA ≥8/10）的带人声成片出来，全程无需人工盯帧。
> 对标比特新语（B 站 Vibe 知识赛道，半月 60 万粉）。配方已对齐（五段叙事 / 76-78BPM /
> 双语字幕 / 单强调色），执行差距用机器化补齐：纪律进任务书、验收进门禁、画面进积木库。

## 一、成果一览（6 条片，全部过闸）

| 成片 | 生成线 | 时长 | QA | 意义 |
|---|---|---|---|---|
| demo-26s | 手工（纸金风） | 26s | — | 画面基线 |
| demo-hook-entropy | SCENE-WRITER 手写 plan | 8s | 8.5 | 四层构图验证 |
| demo-hook-compound | SCENE-WRITER 全自动 | 11.4s | 8.8 | 首条全自动 + 人声 |
| paper-shannon1948 | PAPER2VIDEO 全自动 | 23.8s | 9.5 | 首条论文片 |
| **paper-shannon-deep** | PAPER2VIDEO 章节化 | **180s** | **9.2** | 长视频版（10 场景 32 句旁白） |
| **project-vibe-dsf** | **PROJECT2VIDEO 全自动** | **50s** | **9.1** | 首条项目介绍片（自举） |

## 二、系统架构

```
┌── 内容生成线（三条并行，产出 SCENE-PLAN.json 后汇入同一后半程）─────────┐
│ SCENE-WRITER   主题一句话 ──→ PROMPT.md 任务书 ──→ SCENE-PLAN.json      │
│ PAPER2VIDEO    论文 PDF ──→ paper_text.py ──→ PROMPT-EXTRACT ──→        │
│                PAPER-BRIEF.json ──(validate_brief 闸)──→ PROMPT-SCRIPT │
│ PROJECT2VIDEO  GitHub README ──→ PROMPT-PROJECT ──→ PROJECT-BRIEF.json │
│                ──(validate_brief_project 闸)──→ PROMPT-PROJECT-SCRIPT  │
└──────────────────────────────┬───────────────────────────────────────┘
                               ▼
        SCENE-PLAN.json ──(validate_plan.py 11 组硬闸)──→
        build_html.mjs（积木组装成单文件 HTML）──→
┌── 后半程（100% 共用）────────────────────────────────────────────────┐
│ render_frames.mjs  逐帧截图（CDP fast 模式）→ frames/*.png            │
│ qa_check.py        11 项评分 + avg≥8 硬门禁（exit 1 卡死流水线）      │
│ build_narration.py edge-tts 旁白 + 窗口拟合（tempo≤1.25 只警告）      │
│ synth_bgm.py       确定性 BGM（--marks 场景卡点）                     │
│ synth_sfx.py       六音效卡点合成（impact/riser/tick…docs/17）        │
│ mix_audio.py       RMS 侧链闪避（纯 numpy）                          │
│ build.ps1          ffmpeg 合成（loudnorm -14 LUFS, bt709）→ final.mp4│
└──────────────────────────────────────────────────────────────────────┘
run_all.ps1：五阶段一键串联（渲染→QA闸→BGM→音效/旁白→混音合成），exit 0-4 定位失败段
```

> 目录归属（2026-11-06 企业级重构）：render_frames.mjs → `pipeline/render/`、qa_check.py →
> `pipeline/qa/`、build_narration.py / mix_audio.py → `pipeline/audio/narrate/`、
> synth_bgm.py / wave_png.py → `pipeline/audio/`、build.ps1 → `pipeline/compose/`。
> 完整地图见 CONTRIBUTING.md。

## 三、分层实现要点

### 1. 渲染器 render_frames.mjs
- **CDP fast 模式**（默认开）：一个 Chrome 复用 4 个并行会话长连接截图，0.65→0.13s/帧（**4.9 倍**）；
  headless 必须用 `Emulation.setDeviceMetricsOverride` 锁 1920×1080（窗口含边框的坑）；
  多会话共享 WebSocket 时**消息 id 全局唯一**（各会话独立计数会跨会话错投、截到旧帧）
- 长片预算：0.82s/帧（7 积木长 HTML），180s 片净渲染 ~75min；`--start/--end` 局部重渲
  省下大半时间（必须同时给 `--duration`）
- 机器睡眠会挂死 CDP 连环超时——按 user-data-dir 精确杀 Chrome 后补渲缺段

### 2. 质量门禁 qa_check.py（flash 自评不可信，验收器必须比模型狠）
- **v1 运动结构**（逐帧）：画面密度 / 静止段（≤4s 铁律）/ 硬切（2-6 最佳）/ 边缘溢出 /
  字幕带空档 / 首帧抓人
- **v2 审美**（每秒采样）：纹理能量（正常 7-8%、爆款 ≥11%）/ 构图重心（禁 0.47-0.53 居中癖）/
  强调色占比 / 字幕占用
- **阈值内幕**：变化判定 = |亮度差|>8 且每帧变化像素 ≥0.35%（≈7.2k px @1080p30）；
  慢速漂移新旧位置重叠不计入——**运动要大步或闪烁**；`edge_bleed` 的 `[:10]` 是显示截断
  （全量帧数改看 `edge_bleed_count`，v4 起评分也用它）
- 门禁：avg<8 → exit 1，流水线硬卡，不带病交付
- **v3 时长缩放**（2026-11-06，docs/19）：断点/硬切预算按片长缩放
  （每 20s 一个断点 / 每 15s 一个硬切）——短片与 v2 逐项等价，180s 长片 9.18→9.36；
  `--v2` 可回退；JSON 报告带 `qa_version` + `budgets`
- **v4 画风感知边缘**（2026-11-06，docs/20）：弃用 `edge_max>235` 绝对亮度线——深底只抓纯白
  溢出（中灰漏检）、浅底背景本身就过线（全帧误报）且暗字溢出 `edge_max` 纹丝不动。改为
  "全片中位数定画风 + 相对背景 ±96 灰阶 + 边带异常面积 ≥0.3%"；`--legacy-edge` 可回退。
  实测两条样片 v4 与 v3 分数逐项相同（8.8 / 9.1），异常峰值 0.0% / 0.02%，门槛余量 15 倍；
  `pipeline/qa/test_edge_v4.py` 7 条合成帧断言已接入 CI

### 3. 场景纪律三层机器化（SCENE-WRITER）
- PROMPT.md 任务书（写死设计纪律）→ validate_plan.py（拍点 ±0.5 帧 / 密度 ≥0.12 /
  com_x 禁 0.5 / 字幕不跨场景 / l3 层数下限等 11 组检查）→ build_html.mjs 积木组装
- 五段叙事：hook（成本对撞）→ anchor（是什么）→ reason（为什么，逐章）→ turn（反转）→ land（回声 hook）
- 时间轴对齐拍网格（126BPM → 0.47619s/拍），场景边界落在整拍上，BGM 卡点直接喂

### 4. 积木库 pipeline/blocks/（10 个积木全部过闸入库）
- **深空片**：entropy-burst（粒子爆发）/ data-chart（曲线分叉）/ beat-counter（数字滚动）/
  vs-counters（双数字对撞）/ flow-pipe（节点链管道）/ text-points（要点点亮）/ timeline（年代轴）
- **paper 项目片**：feature-cards（白卡特性）/ terminal-window（暗终端证据窗）/ repo-card（收尾卡）
- **强调语言（用户定调，最高优先）**：数字/圆点/标记落定后**绝对静止——禁呼吸、伸缩、
  脉冲、alpha 闪烁**；强调 = 落定瞬间 accent 下划线一次性扫出后静态保持；运动感一律交给
  巡游光带/粒子流；终端光标闪烁保留。**实测去晃动零代价**（demo 8.5→9.1，shannon 9.2 保持）
- **运动源铁律**：0.35%/帧 ≈7.2k px——细线/微脉冲没面积，怎么动都不够；长场景必须配
  **巡游光带**（110px 宽 accent 微光、两缘 ~10px/帧 ≈9.7k px/帧）或粒子流；入场淡入 ≤0.2s
  （>0.4s 的一次淡入会被 QA 计成连续多次"硬切"）
- 契约：`l2(ctx, T, sc, P, U)`，窗口时间用绝对秒，随机性由 seed 派生（确定性渲染）

### 5. 旁白层 pipeline/audio/narrate/（docs/13）
- provider=**edge-tts**（零 key，zh-CN-YunxiNeural 男声）；本机无 N 卡，CosyVoice 挂起
- 窗口拟合："读法音节 × 4.5 音节/秒"估句长；顿号有停顿要按读法估；超窗**加窗不压速**
  （金句宁加片长），tempo 上限 1.25；TTS 念数字极慢要留余量；语速用 TTS 原生 rate+15%
- mix_audio.py：RMS 侧链闪避（纯 numpy 确定性），验收靠 JSON fit 报告 + 波形目检（agent 听不见）
- 拆句卡点=免费戏：设问放在滚动时、揭晓放在命中后

### 6. 三条内容生成线对比
| 线 | 输入 | 前置新增 | 后半程复用 |
|---|---|---|---|
| SCENE-WRITER | 主题一句话 | PROMPT 任务书 + plan 闸 | 100% |
| PAPER2VIDEO | 论文 PDF | paper_text 提取 + PAPER-BRIEF 闸 + PROMPT-SCRIPT | 100% |
| PROJECT2VIDEO | GitHub 仓库 | PROJECT-BRIEF 闸（proof 必填/metrics 四元组）+ PROMPT-PROJECT-SCRIPT | 100% |
- 新线只需写"拆解任务书 + brief 契约 + 校验器 + 规划衔接任务书"，渲染/QA/旁白/合成零改动
- 系列化：同一项目可出 hook 片 + 深讲片 + 项目片三连发，brief 互通（docs/15 §七）

### 7. paper 风格皮肤（PROJECT2VIDEO，独立站同源设计令牌）
- 浅暖白纸底 #fcfcfa + 墨字 + deep teal #0d6e63 唯一强调 + 暗终端证据窗；hairline 网格纹理
- 浅底专用分支：暗角 α0.086@边中点（**纯视觉设计**；历史上曾用于压住 QA 的 235 亮边检测线，
  v4 起不再是过闸刚需，见 docs/20）、GRAIN 墨点、字幕 en 灰
- 模板改动全部向后兼容（`_probe/` 深空回归夹具 + --stills 探针目检，深空片零变化）

## 四、踩坑知识库（防复发，全部实测档案）

| 坑 | 正解 |
|---|---|
| `String.replace` 字符串 replacement 把 `$'` 当特殊序列，模板后半段插进积木代码→整页黑屏 | 凡 replacement 可能含 `$` 一律函数形式 `replace(x, () => v)` |
| `drawText` 用 `parseInt(font)` 解析 'italic 27px Georgia' → NaN → fillText 静默不画 | `font.match(/([\d.]+)px/)` 抓 px 值 |
| PS 5.1 无 BOM UTF-8 = 乱码 ParserError | .ps1/.bat 全 ASCII 或 UTF-8 BOM |
| EAP=Stop 把原生命令 stderr 变终止错误 | run_all 用 Continue + LASTEXITCODE |
| PowerShell 里 ffmpeg 流信息走 stderr，`2>&1` 不可靠 | 落盘 tmp 文件再解析 |
| imageio-ffmpeg 二进制名带版本号 | build.ps1 用完整路径执行，不靠 Get-Command |
| bash 赋值语句里 glob 不展开（`export PATH="...versions/*..."`） | 写字面版本号 |
| TTS 念数字极慢（"是 37.8 倍"5 字 2.23s） | 读法音节估窗 + 加窗不压速 |
| 慢淡入被计成连续"硬切"（面板 ≈25% 画幅） | 入场统一 ≤0.2s |
| 细线/微脉冲凑不够 0.35%/帧变化底线 | 巡游光带/粒子流当运动源 |
| QA `edge_bleed [:10]` 是显示截断；浅底 252 恒过 235 线、暗字溢出 `edge_max` 却纹丝不动 | 当时靠浅底暗角加强绕过；**QA v4 画风感知检测根治**（docs/20），暗角回归纯视觉设计 |
| CDP 多会话 id 冲突 / headless 边框 / 机器睡眠挂渲染 | 全局唯一 id / setDeviceMetricsOverride / 补渲 |

## 五、设计纪律（定调即法律）

1. **五段叙事**：hook 成本对撞 → anchor 是什么 → reason 为什么 → turn 反转 → land 回声 hook
2. **单强调色**：全片每场景发光 ≤1 个；积木只给 L2 主角染 `U.ACCENT`
3. **构图偏置**：主视觉重心 x ∈ [0.42,0.46] 或 [0.54,0.58]，禁居中
4. **数字只从 brief 来**，终端命令必须是 README 原文，stars 没有就不显示（不编数字）
5. **强调语言**：落定 + 下划线一次性扫出；主体恒定，运动交给环境（光带/粒子）

## 六、下一步（P1）

6. ~~synth_sfx.py 按 CUE-SHEET 卡点合成音效轨~~ ✅ 2026-11-06 落地（docs/17，demo-hook-compound 三层音频首验）
   7. ~~palette.json 品牌契约 + 水印参数化~~ ✅ 2026-11-06 落地（docs/18：palette_name 引用制+水印回落，
      三层优先级 内联>引用>默认）
   8. ~~强模型分工~~ ✅ 2026-11-06 落地（docs/01 §7：创意帧→Opus 5.5 走云雾 env-creative.ps1，
      批量/修补→flash 不变；云雾已迁移 v2.cloudmist.cloud，端点实测 401 鉴权通）
   9. ~~静帧并排评审页~~ ✅ 2026-11-06 落地（pipeline/review.mjs：场景网格+采样三帧+
      A/B 按 segment 对齐；v1.2.0 起联动 qa.json：病灶标红+病灶帧自动补采+QA 汇总卡）
   10. ~~easings.js GSAP 级缓动预设~~ ✅ 2026-11-06 落地（blocks/lib/_easings.js：EASE 19 缓动
      恒定注入，easeOutBack 阻尼定稿值像素一致（SHA256 实测），禁 Elastic/Spring 已成文）
8. 强模型出创意帧 + flash 批量　9. 静帧并排评审页　10. easings.js GSAP 级缓动
- QA v3 想法：长片断点阈值按时长缩放（180s 片天然累积更多静止段）
- 音色 A/B（Yunxi/Yunyang/Xiaoxiao 盲选）；系列化三连发（hook + 深讲 + 项目片，brief 互通）
- 引擎结论（勿再议）：不换 Remotion/Motion Canvas/HyperFrames——引擎不是质量瓶颈

---

*本文为全景索引；各子系统细节见 docs/10（差距分析）、12（SCENE-WRITER）、13（旁白）、
14（论文线）、15（项目线）、pipeline/blocks/README.md（积木契约与铁律）。*
