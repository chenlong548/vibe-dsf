# 17 · SFX 音效层（synth_sfx.py）

> P1 #6 交付。解决的问题：只有 BGM 的片子"MV 感缺一半"——比特新语式观感的另一半
> 来自音效贴着动效走（数字砸下配 impact、卡片飞入配 whoosh、揭晓前 riser 蓄力）。

## 一、设计原则

1. **无采样、无版权、确定性**——与 `synth_bgm.py` 同一哲学：纯 numpy 合成，同一份 plan
   + 同一个 `--seed` 永远得到同一个 wav。
2. **音效是点缀不是铺底**——整条轨 90% 时间接近静音，只在卡点处出现。单发峰
   0.12–0.22（-16 ~ -13 dBFS），混音 bus 里 BGM 是 0.32 增益、旁白 1.0，音效要
   "贴着动效、不抢旁白"。
3. **SFX 不参与旁白闪避**——闪避保护的是"语音可懂度"；音效本来就该跟着画面走，
   被压掉反而破坏音画同步。`mix_audio.py` 里 sfx 直通叠加。
4. **时基契约**：`sfx.t` 是**绝对秒**（与场景边界同系，硬闸第 2 组保证它在拍点网格上）。
   唯一例外 **riser 向前铺**：它的 t 是揭晓点，合成起点 = t − 2.0s——语义是"提前蓄力"。

## 二、六音效白名单（与 validate_plan 第 11 组同源）

| name | 时长 | 峰值 | 合成原理 | 用法 |
|---|---|---|---|---|
| `impact-low` | 0.90s | 0.22 | 90→38Hz 指数扫频 + tanh 饱和 + 噪声瞬态 | 场景切换 / 数字落定 |
| `impact-mid` | 0.60s | 0.18 | 150→70Hz，比 low 快、更"敲" | 卡片 / 面板落定 |
| `tick` | 0.05s | 0.13 | 2.4kHz 纯音 + 极短噪声 | 标记点亮 / 计数步进 |
| `riser` | 2.00s | 0.12 | 一阶低通截止上移 + (t/dur)^2.2 包络 | 揭晓前蓄力（向前铺） |
| `sub-drop` | 0.80s | 0.20 | 55→24Hz 下坠 + 轻饱和 | 反转 / 揭底 |
| `whoosh` | 0.55s | 0.15 | 带通噪声横扫（低通上移 − 低通差分）+ 菱形包络 | 元素飞入 / 转场 |

声像策略：低频类（impact/sub-drop）居中；tick/riser/whoosh 按 15% 左右交替
（`--seed` 决定序列），避免每发都砸正中。

## 三、用法

自动（推荐）：`run_all.ps1` 检测 plan 里任一场景带 `sfx` 数组就自动合成 + 混音：

```powershell
powershell -File pipeline\run_all.ps1 -Project projects\<slug> -Duration 11.43
# [4/5] 会依次输出：synth_sfx 报告 → build_narration 报告（如有）→ mix_audio 报告
```

手动分步：

```powershell
python ../pipeline/audio/synth_sfx.py sfx.wav --plan SCENE-PLAN.json --duration 11.43
python ../pipeline/audio/narrate/mix_audio.py --bgm bgm.wav --sfx sfx.wav \
    --narration narration.wav --duration 11.43 --out final_audio.wav
```

plan 写法（SCENE-PLAN.json 场景内，t 为绝对秒）：

```json
"sfx": [ { "t": 3.81, "name": "impact-low" }, { "t": 3.33, "name": "riser" } ]
```

## 四、验收（agent 听不见，看图）

```powershell
python ../pipeline/audio/wave_png.py sfx.wav wave.png --bpm 126 --marks 3.81,9.52,15.24,19.05
```

目检三件事：① impact 落点正好压在 mark 线上；② riser 是揭晓点前 2s 的渐强包络；
③ 其余时段接近静音。`synth_sfx.py` 的 JSON 报告同时给出 `events / by_name /
skipped / peak_dbfs`——skipped 非空说明 plan 里有越界卡点（<0.05s 或距片尾 <0.05s）。

## 五、混音层级（最终响度账）

| 层 | 增益 | 闪避 | 说明 |
|---|---|---|---|
| 旁白 | 1.0 | — | 主角，loudnorm 后统一 -14 LUFS |
| BGM | 0.32 | duck 9dB（attack 0.12 / release 0.45） | 无人声处满增益 |
| SFX | 1.0（内建 0.12-0.22 峰） | **不闪避** | 贴动效走 |

三层同响时 bus 峰约 -5 dBFS，合成阶段 `loudnorm I=-14` 统一响度，不会削波。
