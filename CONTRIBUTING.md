# CONTRIBUTING — 开发指南

## 目录地图

```
vibe-dsf/
├── pipeline/                  # 核心管线（一键入口：run_all.ps1）
│   ├── run_all.ps1            # 五阶段一键流水线：渲染→QA闸→BGM→旁白混音→合成（exit 0-4 定位失败段）
│   ├── requirements.txt       # Python 依赖（numpy / pillow / edge-tts）
│   ├── render/                # 渲染：render_frames.mjs（CDP fast 模式逐帧截图）
│   ├── qa/                    # 门禁：qa_check.py（11 项评分，avg<8 硬拦截）
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
│   ├── project-vibe-dsf/      # 项目线样片（QA 8.5）
│   ├── _probe/                # 回归夹具（CI 冒烟测试用，勿动）
│   └── _archive/              # 实验归档（保留回退，不再维护）
├── skills/                    # agent 技能包（SKILL.md frontmatter，MIT）
│   ├── vibe-film-ds/          # 主技能：风格 DNA / 四层构图 / 失败模式
│   ├── bgm-synth/             # BGM 合成技能
│   └── qa-gate/               # QA 门禁技能
├── styles/                    # 画风规范（fable / nocturne / paper-gold / romance）
├── scripts/                   # env.ps1（模型锁定）/ setup.ps1（体检）
├── docs/                      # 00-16 编号文档（见 docs/16 全景总结）
└── .github/workflows/ci.yml   # CI：语法检查 + 场景规划冒烟
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

# 分步跑（在项目目录里）
node ..\..\pipeline\render\render_frames.mjs --fps 30 --duration <秒>
python ..\..\pipeline\qa\qa_check.py frames --fps 30 --json qa.json
python ..\..\pipeline\audio\synth_bgm.py bgm.wav --style vibe --duration <秒>
python ..\..\pipeline\audio\synth_sfx.py sfx.wav --plan SCENE-PLAN.json --duration <秒>
python ..\..\pipeline\audio\narrate\build_narration.py SCENE-PLAN.json --out narration.wav
python ..\..\pipeline\audio\narrate\mix_audio.py --narration narration.wav --bgm bgm.wav --sfx sfx.wav --duration <秒> --out final_audio.wav
powershell -File ..\..\pipeline\compose\build.ps1 -Audio final_audio.wav

# 波形目检（agent 听不见，看图验收音频）
python ..\..\pipeline\audio\wave_png.py bgm.wav wave.png --bpm 96 --marks 24,48,60
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
- **运动源铁律**：每帧变化像素 ≥0.35%（≈7.2k px @1080p30）才算"在动"；3px 细线/微脉冲没有面积，怎么动都不够——长场景配巡游光带或粒子流。
- **入场淡入 ≤0.2s**：更长的面板淡入会被 QA 计成连续硬切。
- **长场景**：最长静止段 ≤1.5s 满分 / ≤2.5s 9 分 / ≤4s 7 分，超出直接不及格。

详见 `pipeline/blocks/README.md` 与 `docs/16-PROJECT-SUMMARY.md`。

## 验证流程

改了 `blocks/`、`scene_writer/`、`run_all.ps1` 或任何被引用路径后：

1. CI 会自动跑语法检查 + `_probe` 夹具冒烟（规划闸 + 组装）；
2. 本地跑一次最小端到端：

   ```powershell
   powershell -File pipeline\run_all.ps1 -Project projects\demo-hook-entropy -Duration 8
   ```

3. QA 过闸（avg≥8）才算完成；合成产物 `final.mp4` 人工过目一遍。
4. 渲染产物（frames/*.png、*.wav、*.mp4、qa.json）都在 `.gitignore` 里，**不要提交**；要提交的是 plan/brief JSON 与 index.html。

## 提交约定

- 用 `git mv` 移动文件（保历史）；移动后全局搜旧路径（`grep -rn "旧名"`）同步所有引用——本次重构的引用面：`run_all.ps1`、SKILL.md×3、各脚本头注释、docs 命令示例。
- 渲染参数/QA 分数变化时，同步 `pipeline/blocks/registry.json` 与相关 docs 的分数行。
