# 21 · 一键流水线执行报告（pipeline_report.json）

> 解决的问题：以前 `run_all.ps1` 只有控制台输出 + 散落在项目目录的产物。
> 成功了不知道哪一阶段慢，失败了只看到一行红字，也没有机器可读的执行档案——
> 自动化流水线不该靠翻终端回滚日志来复盘。

## 一、架构：事件流 + 汇总，PowerShell 不拼 JSON

```
run_all.ps1
  ├─ 每阶段：[Stopwatch.Restart] → 执行 → Add-Stage(id,status,seconds,code,message)
  │            └─ python pipeline/report/generate.py --event _pipeline_events.jsonl ...
  ├─ 任一失败：Complete-Report(code, stage, message) → 补一条 failed 事件
  └─ 成功末尾：Complete-Report(0)
                 └─ python generate.py --finalize --events ... --project-dir ...
                       ├─ 读事件流（坏行只计数，不拖垮汇总）
                       ├─ 扫项目目录：帧数 / 8 类产物字节数 / qa.json / SCENE-PLAN.json
                       ├─ 读仓库根 VERSION → pipeline_version
                       └─ 写 <project>/pipeline_report.json
```

三个设计选择：

- **PowerShell 侧一行 JSON 都不拼**。PS 5.1 的 `ConvertTo-Json` 有单元素数组退化、
  UTF-8 BOM、中文 `\uXXXX` 转义等坑；现在 PS 只传 6 个标量参数，结构化全交给 Python，
  报告里的中文是原样的（`ensure_ascii=False`）。
- **事件流 append-only**（`_pipeline_events.jsonl`）。流水线被强杀/崩溃，已完成阶段也留得下，
  不用等 finalize。汇总时坏行记进 `summary.bad_event_lines`。
- **可观测性不能反过来卡住生产**：`generate.py` 自身出错只写一份带 `error` 的最小档案，
  恒定返回 0，绝不改变 `run_all.ps1` 的退出码；`-NoReport` 可完全关掉这一层。

## 二、报告字段

| 组 | 字段 | 说明 |
|---|---|---|
| 元信息 | `schema_version` / `pipeline_version` | 报告结构 1.0；流水线版本读仓库根 `VERSION` |
| 元信息 | `project` / `project_dir` / `started_at` / `finished_at` / `elapsed` | 目录、时区时间戳、总耗时（秒） |
| 结论 | `exit_code` / `verdict` / `failed_stage` | `success` / `qa_blocked`(2) / `failed` / `report_error` |
| 阶段 | `summary` | `stages_total` / `stages_ok` / `stages_skipped` / `stages_failed` / `stage_seconds` / `bad_event_lines` |
| 阶段 | `stages[]` | `ts` / `stage` / `status` / `seconds` / `code` / `message` |
| 画面 | `frames` | `dir` / `count` / `fps` / `duration` / `resolution` |
| 验收 | `qa` | `avg` / `version` / `gate` / `passed` / `worst[]` / `budgets` / `edge` / `issues` / `resolution` |
| 规划 | `plan` | `topic` / `style` / `palette_name` / `scenes` / `subtitles` / `narration_lines` / `sfx_events` / `bpm` … |
| 产物 | `artifacts` | `html` / `plan` / `qa_report` / `bgm` / `sfx` / `narration` / `mix` / `video`；存在给 `bytes`+`mtime`，缺失给 `missing: true` |

`qa.issues` 汇总四类病灶数量：`still_runs` / `cuts` / `edge_bleed_frames`（v4 起取全量
`edge_bleed_count`，不受 `[:10]` 显示截断影响）/ `subtitle_gaps`。
`qa.worst` 是最弱三项评分，直接对应评审页该改的地方。

阶段 id：`preflight`（工具定位、html/ffmpeg 检查）、`render`、`qa`、`bgm`、
`audio`（SFX + 旁白 + 混音）、`compose`。失败时 `failed_stage` 取最后一条 `failed` 事件；
若连一条事件都没有（极早期失败），标 `preflight`。

## 三、退出码与报告的关系

| exit | 含义 | verdict | 是否产出报告 |
|---|---|---|---|
| 0 | 全链成功 | `success` | ✅ |
| 1 | 渲染 / 前置检查失败 | `failed` | ✅（preflight / render） |
| 2 | QA 闸门拦截 | `qa_blocked` | ✅（`failed_stage=qa`） |
| 3 | BGM 或 ffmpeg 合成失败 | `failed` | ✅ |
| 4 | 音效 / 旁白 / 混音失败 | `failed` | ✅ |

**唯一例外**：连 Python 都定位不到时无法生成报告（报告器本身是 Python），此时退化为
原来的控制台报错。除此之外，所有 `exit` 都收敛到 `Complete-Report` 这一个出口。

报告与事件流都是可重建产物，已加入 `.gitignore`（与 `qa.json` / `review.html` 同级）。

## 四、怎么用

```powershell
# 正常跑，报告自动出现在项目目录
powershell -File pipeline\run_all.ps1 -Project projects\<slug> -SkipRender

# 看结论（机器读 JSON，人读这一行也够）
python -c "import json;d=json.load(open('projects/<slug>/pipeline_report.json',encoding='utf-8'));print(d['verdict'],d['exit_code'],d['summary'])"

# 应急关掉报告层
powershell -File pipeline\run_all.ps1 -Project projects\<slug> -NoReport

# 单独重放/汇总（调试报告器时）
python pipeline\report\generate.py --finalize --events projects\<slug>\_pipeline_events.jsonl `
  --project-dir projects\<slug> --exit-code 0 --elapsed 57.85 --fps 30
```

`run_all` 控制台末尾会打印 `[report] pipeline_report.json · exit 0 · 5 阶段 · 57.85s · QA 8.82`。
PS 5.1 会把 Python 的 UTF-8 stdout 按 ANSI 解码，控制台里这行中文可能显示为乱码——
**JSON 文件本身是正常 UTF-8，退出码与内容都不受影响**。

## 五、实测（2026-11-06）

成功路径（demo-hook-compound，`-SkipRender`）：

```
exit 0 / verdict success / elapsed 57.85s / 5 阶段（4 ok + 1 skipped）
render 0.053s · qa 32.67s · bgm 1.837s · audio 11.905s · compose 9.064s
frames 343 @1920x1080 / QA 8.82 (v4, passed) / plan 3 场景 4 句旁白 4 个 SFX
artifacts 8/8 齐全（无 missing）
```

失败路径（30 帧全黑夹具，QA 6.55）：

```
exit 2 / verdict qa_blocked / failed_stage qa / elapsed 1.96s
stages: render skipped → qa failed「QA 闸门拦截（总分 < 8）」
artifacts 只剩 html + qa_report —— 后续阶段确实没跑，报告能直接证明这一点
```

回归夹具 `pipeline/report/test_generate.py`：8 条断言（成功形状 / QA 拦截 / 早期失败 /
合成失败 / 坏事件行 / 缺产物 / CLI 中文往返 / append-only 顺序），纯临时目录、1.9 秒跑完，
已接入 CI。

## 六、纪律

- 加新阶段必须同时：`$stageSw.Restart()` + `Add-Stage <id> ...` + 失败路径
  `Complete-Report <code> <id> "<原因>"`，别再用裸 `exit`。
- 新增产物要进 `generate.py` 的 `ARTIFACT_MAP`，否则报告里查不到。
- 改报告字段结构就递增 `SCHEMA_VERSION`，并在本文件补字段表；下游（评审页、
  系列化批处理）按 `schema_version` 兼容。
- 报告是**观测**，不是门禁：不要在这里加"不达标就 exit 1"，门禁只在
  `pipeline/qa/qa_check.py`。
