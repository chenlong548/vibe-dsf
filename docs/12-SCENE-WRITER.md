# 12 · SCENE-WRITER：场景规划自动化（把"设计纪律"编译成机器约束）

> 解决什么：流水线此前最大的隐性成本——**每个场景要靠人想清楚、写清楚**。
> 引擎不是瓶颈（见 11-FRAMEWORK-RESEARCH），瓶颈是"规划"这个纯人工环节。
> 本文档是通用方法论：任何主题、任何人（包括不写代码的协作者）都可复用。

---

## 一、思路：人从"写场景"退到"给主题 + 审片"

质量差距来自设计纪律（四层构图 / 密度预算 / 拍点对齐 / 构图偏置）。这些纪律
**本来就被写成了文档和 QA 阈值**——那就不该再要求人脑记住它们。三层机器化：

| 层 | 机器约束 | 文件 |
|---|---|---|
| 生成时 | 万能任务书：LLM 按硬约束清单产出结构化规划 | `pipeline/scene_writer/PROMPT.md` |
| 落地前 | 规划硬闸：11 组检查，违规清单打回重写 | `pipeline/scene_writer/validate_plan.py` |
| 渲染时 | 积木组装：场景 = 选积木 + 填参数，代码零手写 | `pipeline/blocks/` + `build_html.mjs` |

人的新角色：**一句话主题 → 看过闸成片 → 说行/不行。**

## 二、四步链路（全部已实测跑通）

```
① 一句话主题 ──(任何 LLM × PROMPT.md)──▶ SCENE-PLAN.json
② validate_plan.py ──▶ 违规清单 / 放行          （exit 1 = 打回重写）
③ build_html.mjs ──▶ projects/<slug>/index.html （template + blocks 自动组装）
④ render_frames → qa_check（avg≥8 硬门禁）→ build.ps1 ──▶ final.mp4
```

命令（在仓库根目录）：

```bash
python pipeline/scene_writer/validate_plan.py projects/<slug>/SCENE-PLAN.json
node pipeline/scene_writer/build_html.mjs --plan projects/<slug>/SCENE-PLAN.json --out projects/<slug>/index.html
cd projects/<slug>
node ../../pipeline/render_frames.mjs --duration <秒> --fps 30
python ../../pipeline/qa_check.py frames/ --fps 30
powershell -File ../../pipeline/build.ps1        # 需 DSH_FFMPEG_PATH 指向 imageio 的 ffmpeg
```

## 三、SCENE-PLAN 是什么

一个 JSON：meta（主题/时长/BPM/调色板）+ scenes 数组（每场景：五段叙事段位、
起止时间【必须对齐拍点】、L1 支撑、L2 积木与参数、L3 标注、卡点、音效提示）+
subtitles 数组（中英双语，不得跨场景）。完整契约见 `SCENE-PLAN.schema.md`。

关键设计：
- **时间轴是推导出来的，不是感觉出来的**：所有边界落在 60/BPM 拍点网格（±0.5 帧），
  BGM 卡点天然对齐
- **密度预算前置**：area_pct + L1 + L3 条数在规划层就估出来，低于 0.12 根本不进渲染，
  不浪费渲染时间才知道"画面空"
- **字幕不跨场景**：跨切字幕是观感杀手，校验器直接挂

## 四、积木库（blocks）

学 HyperFrames registry blocks 的思想，落在自研 render(t) 契约上：

| block | 用途 | QA 记录 |
|---|---|---|
| `entropy-burst` | 粒子爆发/能量释放（钩子爆点） | 8.5/10 @ demo-hook-entropy |
| `data-chart` | 双曲线分叉（自带生长式坐标轴） | 9.1/10 @ demo-hook-compound |
| `beat-counter` | 大数字滚动 + 公式框 | 9.1/10 @ demo-hook-compound |
| `vs-counters` | 双数字对撞（右侧胜出染强调色） | 9.1/10 @ demo-hook-compound |

铁律：**过 QA 才入库**；随机性全靠 seed；每场景发光 ≤1；强调色只染主角。
新增流程见 `pipeline/blocks/README.md`。

## 五、实测记录（首条全自动片）

- 主题输入：仅一行"复利效应，9.5 秒钩子"
- 规划：3 场景（hook 曲线分叉 → anchor 数字锚 37.8 → land 双数字对撞），20 拍 @126BPM
- 校验：首轮过闸（修过校验器自身 2 个 bug：argparse 漏导入、registry 路径基准）
- QA：**9.1/10 通过**（熵增 demo 人工精调是 8.5）——首条不经人手写场景的片子
  分数反而更高，因为规划层就带上了全部硬约束
- 已知弱项（不卡门禁，记录在案）：
  - 首帧抓人 6/10、画面充实 7/10：曲线类积木的像素变化量天然低于粒子类
  - 积木改进方向：data-chart 加"曲线末端生长爆点"、S3 结尾加持续微运动元素

## 六、迭代闭环（改东西只动 JSON）

改文案/换数字/调节奏 = 改 `SCENE-PLAN.json` → ②③④ 重跑。渲染 0.13s/帧，
9.5s 片全量重渲 + QA ≈ 1 分钟。**不存在"改一行文案要重新手写 HTML"这件事。**

## 七、后续（P1 衔接）

- TTS 旁白层（最高优先）：plan 已预留 `narration` 字段，CosyVoice/Fish Audio 接入后旁白随规划一起生成
- synth_sfx.py：scenes[].sfx 已带卡点音效清单，直接消费
- palette.json 品牌契约：meta.palette 将从品牌文件注入，保证全频道同一套色
- 组件库扩容：每做一条新片，把表现好的画面提炼成新积木入库
