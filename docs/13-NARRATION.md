# 13 · 旁白层（TTS）：比特新语有人声，我们也有了

> 解决什么：流水线此前零人声——这是与比特新语之间最后一块短板（引擎与规划已解决，见 11/12 号文档）。
> 2026-11-05 起接入：**SCENE-PLAN 写 narration 数组 → 全自动合成、对齐、闪避混音、进片**。
> 本轮实测：demo-hook-compound 首个带人声成片，四句旁白零截断、卡点对齐、BGM 自动闪避。

---

## 一、链路

```
SCENE-PLAN.narration = [{text, t_in, t_out}, …]
   │  ① build_narration.py（provider 合成 → 窗口拟合 → 按 t_in 铺轨）
   ▼
narration.wav（44.1k mono，全片长）
   │  ② mix_audio.py（BGM 侧链闪避：有人声处 BGM 自动压低 9dB）
   ▼
final_audio.wav（44.1k stereo）
   │  ③ ffmpeg mux + loudnorm（I=-14）
   ▼
final_narrated.mp4
```

一键：`run_all.ps1` 已集成 —— **plan 带 narration 数组时自动跑旁白阶段**，没有则跳过：

```powershell
powershell -File ..\..\pipeline\run_all.ps1 -Duration 11.43 -BgmStyle vibe -Bpm 126
```

## 二、provider 选型判据（2026-11-05 实测定论）

| provider | 状态 | 前提 | 结论 |
|---|---|---|---|
| **edge-tts** | ✅ 当前启用 | 免费、零 key、仅需网络 | 本机**无 N 卡**（实测 nvidia-smi 无输出），这就是当下正解；Yunxi 男声讲解感强 |
| CosyVoice 本地 | ⏸ 挂起 | **N 卡 ≥8G 显存** + 装环境 | 音色天花板更高，待有 GPU 机器再启用 |
| Fish Audio API | ⏸ 备选 | API key | 免费额度可用，需注册 |

换引擎契约：实现 `synthesize(text, out_wav, voice, rate)` → 44.1k mono s16 wav（见 `tts_edge.py` 头注释）。
对齐与混音工程与引擎解耦，**换音色不动链路**。

## 三、实测踩坑（重要，防复发）

1. **TTS 念数字极慢**：`是 37.8 倍。`（5 字）实测 2.23s —— 数字会被念成"三十七点八"。估算句长
   必须按"读法音节"算，不能按字数。数字句要么拆句（见下），要么留足窗口。
2. **金句禁止压速**：punch 线超窗时**宁可延长片长**（本片从 9.52s → 11.43s，+4 拍），
   也不要 atempo > 1.25 —— 金句加速 = 毁情绪。
3. **拆句卡点是免费的戏**：`1.01 的 365 次方`（数字滚动时）+ `是 37.8 倍。`（计数爆走命中后）
   —— 语速问题顺带变成揭晓节奏。
4. **语速用 TTS 原生 rate，别用 ffmpeg atempo**：`+15%` 是韵律级加速（自然）；atempo 1.2+
   是机械压缩（赶）。只有超出 rate 能力的小幅修整才用 atempo（≤1.25 硬上限）。
5. **旁白允许跨场景切**（校验器只禁字幕跨切）：句子跨切是自然语流，本片 n2 就跨了 S2→S3 切点。

## 四、文件

| 文件 | 职责 |
|---|---|
| `pipeline/narrate/tts_edge.py` | provider：edge-tts → 44.1k mono wav（单句自测可 CLI） |
| `pipeline/narrate/build_narration.py` | 逐句合成 → 窗口拟合（超窗 atempo≤1.25 只警告不截断）→ 铺全片底轨，输出 JSON 报告（每句 raw/atempo/fit） |
| `pipeline/narrate/mix_audio.py` | 50ms RMS 包络 → attack 0.12s/release 0.45s 平滑 → BGM 闪避；纯 numpy 确定性 |
| `pipeline/run_all.ps1` | 第 4 阶段（plan 带 narration 自动启用） |

## 五、验收方法（agent 听不见，只能看）

- `build_narration` 的 JSON 报告：每句 `fit` 字段（natural/tempo/over）+ 截断标记
- `wave_png.py final_audio.wav wave.png` 目检：人声包络位置 = 规划窗口、句间 BGM 低垫、无削顶
- 峰值：混音输出 -6 dBFS 左右为健康（loudnorm 在 mux 阶段统一到 -14 LUFS）

## 六、后续

- 音色 A/B：Yunxi vs Yunyang vs Xiaoxiao（同一段文案三版盲选）
- 情感标记：edge-tts 支持 pitch 参数，punch 句可试 -2Hz 低沉
- 有 N 卡机器后：CosyVoice 接入 provider 位，音色克隆（3s 样本）打造频道专属声线
- plan 可加 per-item `voice` / `rate` 覆盖（build_narration 已支持，run_all 用全局默认）
