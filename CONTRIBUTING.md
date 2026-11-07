# CONTRIBUTING — 开发指南

## 目录地图

```
vibe-dsf/
├── pipeline/                  # 核心管线（一键入口：run_all.ps1）
│   ├── run_all.ps1            # 五阶段一键流水线：渲染→QA闸→BGM→旁白混音→合成（exit 0-4 定位失败段；每次产出执行报告）
│   ├── review.mjs             # 静帧评审页生成器：场景网格 + A/B 对比 + QA 病灶叠加（docs/10 #9）
│   ├── requirements.txt       # Python 依赖（numpy / pillow / edge-tts）
│   ├── palette.json           # 品牌契约：账号水印 + 已验证配色库（plan 用 palette_name 引用，docs/18）
│   ├── render/                # 渲染：render_frames.mjs（CDP fast 模式逐帧截图）
│   ├── qa/                    # 门禁：qa_check.py（11 项评分，avg<8 硬拦截）+ test_edge_v4.py（边缘回归夹具）
│   ├── report/                # 执行报告：generate.py（事件流→pipeline_report.json）+ test_generate.py（docs/21）
│   ├── audio/                 # 音频：synth_bgm.py（BGM）/ synth_sfx.py（音效）/ wave_png.py（波形验收）
│   │   └── narrate/           # 旁白：tts_edge.py / build_narration.py / mix_audio.py（闪避混音）
│   ├── compose/               # 合成：build.ps1（Windows）/ build.sh（macOS/Linux）
│   ├── blocks/                # 积木组件库：lib/*.js ×10 + registry.json（QA 分数档案）
│   ├── scene_writer/          # 场景规划线：PROMPT.md / template.html / build_html.mjs / validate_plan.py
│   ├── paper2video/           # 论文→视频线：paper_text.py / validate_brief.py / PROMPT-*.md
│   └── project2video/         # 项目→视频线：validate_brief_project.py / PROMPT-*.md
├── projects/                  # 样片工作区（每片一目录）
│   ├── demo-hook-entropy/     # 正式样片（QA 9.1）
│   ├── demo-hook-compound/    # 正式样片（QA 8.8）
│   ├── paper-shannon1948/     # 论文线样片（QA 9.5）
│   ├── paper-shannon-deep/    # 论文深讲长片（QA 9.2）
│   ├── project-vibe-dsf/      # 项目线样片（QA 9.1）
│   ├── _probe/                # 回归夹具（CI 冒烟测试用，勿动）
│   └── _archive/              # 实验归档（保留回退，不再维护）
├── brand/                     # 品牌资产：logo.svg / favicon.svg / BRAND.md（对外单一真相）
├── site/                      # 可发布双语展示页：index.html / og-card.svg / favicon.svg / check.py
├── skills/                    # agent 技能包（SKILL.md frontmatter，MIT）
│   ├── vibe-film-ds/          # 主技能：风格 DNA / 四层构图 / 失败模式
│   ├── bgm-synth/             # BGM 合成技能
│   └── qa-gate/               # QA 门禁技能
├── styles/                    # 画风规范（fable / nocturne / paper-gold / romance）
├── scripts/                   # verify.py（MVP 一键验收）/ setup.ps1（体检）/ env*.ps1（模型环境）
├── docs/                      # 00-25 编号文档（24 MVP 发布面 / 25 升级计划；见 docs/16 全景总结）
└── .github/workflows/ci.yml   # CI：python scripts/verify.py（与本地同一套 9 项验收）
```

**依赖方向**（保持单向，不加反向引用）：

```
三条内容生成线（scene_writer / paper2video / project2video）
        │  产出 SCENE-PLAN.json
        ▼
blocks（组件库）──被──> build_html.mjs 组装
        │
        ▼
后半程 100% 共用：render → qa → audio → compose
        （run_all.ps1 串联全部阶段）
```

## 环境搭建

Windows 主路径（macOS/Linux 用 `compose/build.sh` 替代合成步骤）：

```powershell
pip install -r pipeline/requirements.txt     # numpy / pillow / edge-tts
node -v                                      # 需 18+
powershell -File scripts\setup.ps1           # 只读体检
# ffmpeg：python -m pip install imageio-ffmpeg，或 winget install Gyan.FFmpeg
```

模型环境（flash 锁定）：复制 `scripts/env.ps1` 的思路，把 API Key 填在自己本地的副本里。

**密钥纪律**：`scripts/env.ps1` 里的 token 永远保持占位符；真实 key 只存在于本地未提交的副本。提交前自查 `git diff` 不含任何 key 片段。

## 常用命令

```powershell
# 一键全流程（在仓库根目录）
powershell -File pipeline\run_all.ps1 -Project projects\<slug> -Duration <秒>
# 可选：-Start 12 -End 18（局部重渲）| -SkipRender | -NoGate | -BgmStyle vibe -Bpm 126
# 退出码：0 成功 / 1 渲染 / 2 QA拦截 / 3 BGM或合成 / 4 旁白
# 每次运行都产出 <project>/pipeline_report.json（阶段耗时/QA 摘要/产物清单/失败阶段，docs/21）
python -c "import json;d=json.load(open(r'projects\<slug>\pipeline_report.json',encoding='utf-8'));print(d['verdict'],d['summary'],d['qa']['avg'])"

# 分步跑（在项目目录里）
node ..\..\pipeline\render\render_frames.mjs --fps 30 --duration <秒>
python ..\..\pipeline\qa\qa_check.py frames --fps 30 --json qa.json
python ..\..\pipeline\qa\qa_check.py frames --fps 30 --legacy-edge   # 只回退边缘检测（= v3 口径，同帧对比）
python ..\..\pipeline\qa\qa_check.py frames --fps 30 --v2             # v2 全口径回退（固定阈值 + 绝对亮度边缘）
python ..\..\pipeline\qa\test_edge_v4.py                              # 边缘检测回归夹具（CI 也跑，纯合成帧）
python ..\..\pipeline\audio\synth_bgm.py bgm.wav --style vibe --duration <秒>
python ..\..\pipeline\audio\synth_sfx.py sfx.wav --plan SCENE-PLAN.json --duration <秒>
python ..\..\pipeline\audio\narrate\build_narration.py SCENE-PLAN.json --out narration.wav
python ..\..\pipeline\audio\narrate\mix_audio.py --narration narration.wav --bgm bgm.wav --sfx sfx.wav --duration <秒> --out final_audio.wav
powershell -File ..\..\pipeline\compose\build.ps1 -Audio final_audio.wav

# 波形目检（agent 听不见，看图验收音频）
python ..\..\pipeline\audio\wave_png.py bgm.wav wave.png --bpm 96 --marks 24,48,60

# 静帧评审页（以下三条在仓库根目录跑；场景网格 + A/B 对比 + QA 病灶叠加）
# 自动读项目里的 qa.json：静止段/硬切/溢出标红，病灶帧自动补采（红框）
node pipeline\review.mjs --project projects\<slug>
node pipeline\review.mjs --project projects\<slugA> --compare projects\<slugB>
node pipeline\review.mjs --project projects\<slug> --qa path\to\qa.json   # 手动指定报告
```

## 加一块积木

1. 写 `pipeline/blocks/lib/<name>.js`：纯绘制函数 `render(ctx, P, T, U)`，**无 import/export**（组装时按序拼接进 `<script>`）；
2. `pipeline/blocks/registry.json` 注册：name / 文件 / params 表 / qa 分数（首次可 `null`）；
3. 过硬闸：`python pipeline/scene_writer/validate_plan.py <plan.json>` —— 计划里引用未注册积木会被拦截；
4. 组装实测：`node pipeline/scene_writer/build_html.mjs --plan <plan> --out projects/<slug>/index.html`；
5. 渲染 + QA 实测，拿到 avg 分数后**回写 registry.json 的 qa 字段**（分数档案是积木可信度的一部分）；
6. 更新 `pipeline/blocks/README.md` 积木表。

## 设计纪律（QA 实测沉淀，改积木前先读）

- **强调语言**：数字/圆点/标记落定后绝对静止——禁呼吸/伸缩/脉冲/alpha 闪烁；强调 = 落定瞬间 accent 下划线一次性扫出后静态保持；运动感交给巡游光带/粒子流。
- **缓动纪律（P1 #10）**：GSAP 级 19 缓动全集在 `blocks/lib/_easings.js`（`EASE` 命名空间，build_html 恒定注入）；easeOutBack 是阻尼版定稿值（历史像素一致），只准一次性入场用；**禁 Elastic/Spring 振荡缓动**（库里故意不提供）。
- **运动源铁律**：每帧变化像素 ≥0.35%（≈7.2k px @1080p30）才算"在动"；3px 细线/微脉冲没有面积，怎么动都不够——长场景配巡游光带或粒子流。
- **入场淡入 ≤0.2s**：更长的面板淡入会被 QA 计成连续硬切。
- **安全区口径（QA v4，docs/20）**：不再用绝对亮度 235 判溢出；按全片中位数定深/浅画风，
  边带内「偏离背景 ±96 灰阶」的像素占比 ≥0.3% 才算。别再用「加强暗角把边缘亮度压到 235
  以下」去迁就检测器——浅底暗色文字溢出时 `edge_max` 纹丝不动，旧口径根本看不见。
  改阈值必须跑 `pipeline/qa/test_edge_v4.py` + 两条实片同帧对比。
- **长场景**：最长静止段 ≤1.5s 满分 / ≤2.5s 9 分 / ≤4s 7 分，超出直接不及格。

详见 `pipeline/blocks/README.md` 与 `docs/16-PROJECT-SUMMARY.md`。

## 验证流程

改了 `blocks/`、`scene_writer/`、`run_all.ps1` 或任何被引用路径后：

1. 先跑 `python scripts/verify.py`（9/9 PASS 才算 MVP READY）；CI 跑的是同一条命令，
   覆盖版本同步、发布面文件、Python / Node 语法、`_probe` 规划硬闸 + 组装冒烟、
   `qa/test_edge_v4.py`、`report/test_generate.py`、`site/check.py`。
   发布面定义在 `docs/24-MVP.md`，`docs/25-ROADMAP.md` 里的计划项不进验收；
2. 本地跑一次最小端到端：

   ```powershell
   powershell -File pipeline\run_all.ps1 -Project projects\demo-hook-entropy -Duration 8
   ```

3. QA 过闸（avg≥8）才算完成；合成产物 `final.mp4` 人工过目一遍。
4. 改了 `run_all.ps1` 还要核对 `<project>/pipeline_report.json` 的 `verdict` /
   `failed_stage` 与实际退出码一致；失败路径同样要产出报告。
5. 渲染产物（frames/*.png、*.wav、*.mp4、qa.json、pipeline_report.json、
   _pipeline_events.jsonl）都在 `.gitignore` 里，**不要提交**；要提交的是 plan/brief JSON 与 index.html。

## 提交约定

- 用 `git mv` 移动文件（保历史）；移动后全局搜旧路径（`grep -rn "旧名"`）同步所有引用——本次重构的引用面：`run_all.ps1`、SKILL.md×3、各脚本头注释、docs 命令示例。
- 渲染参数/QA 分数变化时，同步 `pipeline/blocks/registry.json` 与相关 docs 的分数行。

## 版本纪律（每次推送 GitHub 必做）

版本号在根目录 `VERSION`，语义化（MAJOR.MINOR.PATCH）。**每一次 push 都对应一个新版本**：

1. 按变更性质递增 `VERSION`：功能/工具增强 → MINOR；修 bug / 文档同步 → PATCH；
   破坏性改动（render 契约、SCENE-PLAN 格式不兼容）→ MAJOR。
2. `CHANGELOG.md` 顶部加 `## [X.Y.Z] - YYYY-MM-DD` 条目（Added / Changed / Fixed / Notes）。
3. 提交时**必须包含 `VERSION` 与 `CHANGELOG.md`**（CI 守卫会检查 CHANGELOG 是否含当前版本）。
4. 打附注 tag 并一起推送：

   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z: 一句话说明"
   git push origin main && git push origin vX.Y.Z
   ```

5. README 双语的版本行同步（当前版本 + CHANGELOG 链接）。

基线：`v1.0.0` = 企业级结构重组 + P1 清单全部完成；之后每次提交顺延。
