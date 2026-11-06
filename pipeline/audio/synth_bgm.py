#!/usr/bin/env python3
"""
synth_bgm.py —— 用 numpy 合成一条"纪录片感"的 BGM（无采样、无版权问题）

为什么程序化配乐：代码出片是确定性的，配乐也应该是。
同一份脚本、同一个 --seed，永远得到同一个 wav —— 和 render(t) 一个道理。

用法：
  python ../pipeline/audio/synth_bgm.py bgm.wav --bpm 77 --duration 26
  python ../pipeline/audio/synth_bgm.py bgm.wav --bpm 77 --duration 140 --key Am
"""
import argparse
import wave
import numpy as np

SR = 44100
A4 = 440.0
NAMES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6,
         'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


def freq(note: str, octave: int) -> float:
    return A4 * 2 ** ((NAMES[note] + (octave - 4) * 12 - 9) / 12)


# 四个和弦，覆盖整条片子的情绪走向：困惑 → 揭示 → 推演 → 回落
PROGRESSIONS = {
    'Am': [
        [('A', 2), ('E', 3), ('A', 3), ('C', 4)],     # Am
        [('F', 2), ('C', 3), ('F', 3), ('A', 3)],     # F
        [('C', 3), ('G', 3), ('C', 4), ('E', 4)],     # C
        [('G', 2), ('D', 3), ('G', 3), ('B', 3)],     # G
    ],
}


def pad_voice(f0, dur, rng, detune=0.0015, bright=1.0):
    """一个加法合成的 pad 音色：多个泛音 + 轻微失谐 + 慢速颤音"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1.0 + 0.0022 * np.sin(2 * np.pi * 0.17 * t + rng.uniform(0, 6.28))
    out = np.zeros(n)
    for h in range(1, 7):
        amp = (1.0 / h ** 1.7) * (bright ** (h - 1))
        det = 1.0 + detune * (rng.uniform(-1, 1))
        ph = rng.uniform(0, 6.28)
        out += amp * np.sin(2 * np.pi * f0 * h * det * t * vib + ph)
    return out


def envelope(n, attack, release, sr=SR):
    env = np.ones(n)
    a = min(int(attack * sr), n)
    r = min(int(release * sr), n)
    if a > 0:
        env[:a] = np.linspace(0, 1, a) ** 1.6
    if r > 0:
        env[-r:] *= np.linspace(1, 0, r) ** 1.4
    return env


def pluck(f0, dur, rng, decay=6.0):
    """拨弦/槌击：起音快、指数衰减、泛音随音高衰减"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for h in range(1, 5):
        out += (1.0 / h ** 1.3) * np.sin(2 * np.pi * f0 * h * t + rng.uniform(0, 6.28))
    env = np.exp(-decay * t) * (1 - np.exp(-400 * t))
    return out * env


def mix(buf, start, seg, pan=1.0):
    """把 seg 叠加到 buf 的第 start **秒**，越界自动裁剪（尾部和弦会超出）

    注意：start 的单位是秒，不是采样点。这里乘 SR 是想当然踩过的坑——
    漏乘的话所有音频会被挤进开头几秒，后面全是静音，而 volumedetect
    仍然会给出一个"看起来正常"的平均值，极难发现。用 ../pipeline/audio/wave_png.py 看波形才能抓到。
    """
    s = max(0, int(start * SR))
    if s >= len(buf):
        return
    seg = seg[:len(buf) - s]
    buf[s:s + len(seg)] += seg * pan


def build(duration, bpm, seed):
    rng = np.random.default_rng(seed)
    n = int(duration * SR)
    L = np.zeros(n + SR * 3)
    R = np.zeros(n + SR * 3)

    beat = 60.0 / bpm
    bar = beat * 4
    chord_len = bar * 2                       # 每个和弦 2 小节
    chords = PROGRESSIONS['Am']

    # 段落：钩子(pad) → 揭示(pad+低音) → 推演(加琶音) → 回落(pad)
    # 元组含义：(起始占比, 结束占比, pad 增益, 琶音增益)
    sections = [(0.00, 0.24, 1.0, 0.0),      # 钩子段：只有 pad —— 之前误写成 0.0，导致开头 24% 静音
                (0.24, 0.50, 1.0, 0.0),
                (0.50, 0.82, 1.0, 1.0),
                (0.82, 1.00, 0.55, 0.0)]

    def gain_at(pos):
        for a, b, g_pad, g_arp in sections:
            if a <= pos < b:
                return g_pad, g_arp
        return 0.55, 0.0

    pos = 0.0
    idx = 0
    while pos < duration:
        chord = chords[idx % len(chords)]
        g_pad, g_arp = gain_at(pos / duration)

        # ---- pad ----
        for i, (note, octv) in enumerate(chord):
            f = freq(note, octv)
            dur = chord_len + 2.0                          # 与下一个和弦交叠 2 秒
            v = pad_voice(f, dur, rng, detune=0.0016, bright=0.86)
            env = envelope(len(v), attack=1.6, release=2.2)
            amp = 0.20 / (1 + 0.25 * i)
            seg = v * env * amp * g_pad
            s = pos
            mix(L, s, seg, 0.94 + 0.06 * i)
            mix(R, s, seg, 1.06 - 0.06 * i)

        # 低音：只保留根音下方一个八度
        root_note, root_oct = chord[0]
        sub_f = freq(root_note, root_oct - 1)
        sub = pad_voice(sub_f, chord_len + 2.0, rng, detune=0.0008, bright=0.5)
        sub_env = envelope(len(sub), attack=2.0, release=2.4)
        sub = sub * sub_env * 0.13 * g_pad
        mix(L, pos, sub)
        mix(R, pos, sub)

        # ---- 琶音（推演段）----
        if g_arp > 0:
            steps = int(chord_len * 2)                     # 八分音符
            tones = [freq(nm, oc) * 2 for nm, oc in chord]
            for k in range(steps):
                tt = pos + k * beat * 0.5
                if tt >= duration:
                    break
                f = tones[k % len(tones)]
                p = pluck(f, 1.2, rng, decay=5.0)
                p *= 0.055 * g_arp * (1.0 if k % 4 == 0 else 0.55)
                panned = 0.5 + 0.4 * np.sin(k * 0.9)
                mix(L, tt, p, 1 - panned)
                mix(R, tt, p, panned)

        pos += chord_len
        idx += 1

    # ---- 母带：淡入淡出 + 软限幅 ----
    L, R = L[:n], R[:n]
    fade = int(1.2 * SR)
    ramp = np.linspace(0, 1, fade) ** 1.5
    L[:fade] *= ramp
    R[:fade] *= ramp
    tail = int(2.0 * SR)
    L[-tail:] *= np.linspace(1, 0, tail) ** 1.2
    R[-tail:] *= np.linspace(1, 0, tail) ** 1.2

    peak = max(np.abs(L).max(), np.abs(R).max())
    if peak > 0:
        L *= 0.72 / peak
        R *= 0.72 / peak
    L = np.tanh(L * 1.1) / 1.1
    R = np.tanh(R * 1.1) / 1.1
    return L, R


def write_wav(path, L, R):
    data = np.stack([L, R], axis=1)
    pcm = np.clip(data * 32767, -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# =====================================================================
# vibe 模式：那类片子常见的电子氛围
#   脉冲低音（每拍一下）+ 16 分琶音 + pad + 侧链 + 冲击音 + 上升音效
#   目标听感：冷、稳、有推进感，不抢字幕
# =====================================================================

def kick(dur=0.42, f0=96, f1=44, rng=None):
    """软脉冲：音高快速下滑的正弦，代替采样底鼓"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 42)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t * 9.0)
    click = np.exp(-t * 160) * 0.25
    return (body + click) * 1.0


def sub_pulse(f0, dur=0.5, rng=None):
    """低音脉冲：正弦 + 轻微饱和"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 5.5)
    return np.tanh(x * 1.6) / 1.6


def arp_note(f0, dur=0.42, bright=1.0, rng=None):
    """16 分琶音：两个泛音 + 快速衰减，带一点点金属感"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f0 * t) + 0.45 * bright * np.sin(2 * np.pi * f0 * 2.01 * t) \
        + 0.22 * bright * np.sin(2 * np.pi * f0 * 3.02 * t)
    env = np.exp(-t * 16) * (1 - np.exp(-500 * t))
    return x * env


def riser(dur=2.4, rng=None):
    """上升噪声：段落切换前的推力"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # 简易一阶低通，截止频率随时间上移
    out = np.zeros(n)
    a = 0.02 + 0.9 * (t / dur) ** 2
    y = 0.0
    for i in range(n):
        y += a[i] * (noise[i] - y)
        out[i] = y
    return out * (t / dur) ** 2.2


def impact(dur=1.6, rng=None):
    """冲击音：低频 boom + 短噪声"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (60 * np.exp(-t * 1.2) + 38) * t) * np.exp(-t * 3.4)
    noise = rng.standard_normal(n) * np.exp(-t * 24) * 0.25
    return (boom + noise)


def build_vibe(duration, bpm, seed, marks=()):
    """电子氛围：96BPM 默认，段落由 marks 决定冲击点"""
    rng = np.random.default_rng(seed)
    n = int(duration * SR)
    L = np.zeros(n)
    R = np.zeros(n)

    beat = 60.0 / bpm
    bar = beat * 4
    CHORDS = [
        [('D', 3), ('F', 3), ('A', 3), ('D', 4)],   # Dm
        [('A', 2), ('D', 3), ('F', 3), ('A', 3)],   # Bb/D 近似
        [('F', 2), ('A', 2), ('C', 3), ('F', 3)],   # F
        [('C', 3), ('E', 3), ('G', 3), ('C', 4)],   # C
    ]

    def gain_at(u):
        # 结构：铺 → 进琶音 → 全开 → 退潮 → 再全开
        # 三个返回值分别是 (pad, 琶音, 低音脉冲) 的增益
        if u < 0.18: return 0.72, 0.00, 0.32   # 钩子：只有铺底 + 稀疏心跳
        if u < 0.45: return 0.86, 0.50, 0.62
        if u < 0.75: return 1.00, 1.00, 1.00   # 推演：全开
        if u < 0.88: return 0.55, 0.18, 0.38   # 退潮：留一口气（情绪最低点）
        return 0.96, 0.92, 1.00                # 最后再推起来

    # ---- pad + 低音 ----
    pos, idx = 0.0, 0
    while pos < duration:
        chord = CHORDS[idx % len(CHORDS)]
        g_pad, _, _ = gain_at(pos / duration)
        for i, (nm, oc) in enumerate(chord):
            f = freq(nm, oc)
            v = pad_voice(f, bar * 2 + 2.0, rng, detune=0.0012, bright=0.55)
            v *= envelope(len(v), attack=1.0, release=1.8) * (0.115 / (1 + 0.3 * i)) * g_pad
            mix(L, pos, v, 0.95 + 0.05 * i)
            mix(R, pos, v, 1.05 - 0.05 * i)
        pos += bar * 2
        idx += 1

    # ---- 脉冲低音（每拍）+ 琶音（16 分）----
    total_beats = int(duration / beat)
    for b in range(total_beats):
        tt = b * beat
        u = tt / duration
        g_pad, g_arp, g_pulse = gain_at(u)
        chord = CHORDS[(b // 8) % len(CHORDS)]
        root_nm, root_oc = chord[0]

        # 低音脉冲：每拍，第 1/3 拍重一点
        if g_pulse > 0.05:
            k = sub_pulse(freq(root_nm, root_oc - 1), 0.55, rng)
            amp = 0.20 * g_pulse * (1.0 if b % 4 == 0 else 0.72)
            mix(L, tt, k, amp)
            mix(R, tt, k, amp)

        # 脉冲音（软底鼓）：四拍
        if g_pulse > 0.6:
            kd = kick(0.40, 96, 44, rng)
            mix(L, tt, kd, 0.17 * g_pulse)
            mix(R, tt, kd, 0.17 * g_pulse)

        # 16 分琶音
        if g_arp > 0.05:
            tones = [freq(nm, oc) * 2 for nm, oc in chord]
            for s in range(4):
                ts = tt + s * beat / 4
                if ts >= duration: break
                note = tones[(b * 4 + s) % len(tones)]
                a = arp_note(note, 0.38, bright=0.9, rng=rng)
                amp = 0.052 * g_arp * (1.0 if s == 0 else 0.62)
                pan = 0.5 + 0.42 * np.sin((b * 4 + s) * 0.7)
                mix(L, ts, a, amp * (1 - pan) * 2)
                mix(R, ts, a, amp * pan * 2)

    # ---- 上升音 + 冲击音（按 marks 与段落边界）----
    hit_times = sorted(set([duration * f for f in (0.18, 0.45, 0.75, 0.88)] + list(marks)))
    for ht in hit_times:
        if 0 < ht < duration:
            imp = impact(1.7, rng)
            mix(L, ht, imp, 0.20)
            mix(R, ht, imp, 0.20)
            r = riser(2.2, rng)
            mix(L, max(0, ht - 2.2), r, 0.10)
            mix(R, max(0, ht - 2.2), r, 0.10)

    # ---- 母带 ----
    fade = int(1.0 * SR)
    ramp = np.linspace(0, 1, fade) ** 1.4
    L[:fade] *= ramp; R[:fade] *= ramp
    tail = int(2.4 * SR)
    L[-tail:] *= np.linspace(1, 0, tail) ** 1.2
    R[-tail:] *= np.linspace(1, 0, tail) ** 1.2

    peak = max(np.abs(L).max(), np.abs(R).max())
    if peak > 0:
        L *= 0.80 / peak; R *= 0.80 / peak
    L = np.tanh(L * 1.25) / 1.25
    R = np.tanh(R * 1.25) / 1.25
    return L, R


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--style', choices=['ambient', 'vibe'], default='ambient',
                    help='ambient=纪录片慢速（77）；vibe=电子氛围（96，那类片子的常用听感）')
    ap.add_argument('--bpm', type=float, default=None)
    ap.add_argument('--duration', type=float, default=26)
    ap.add_argument('--seed', type=int, default=20261020)
    ap.add_argument('--marks', type=str, default='',
                    help='冲击点秒数，逗号分隔，如 "24,48"')
    a = ap.parse_args()

    bpm = a.bpm if a.bpm else (96 if a.style == 'vibe' else 77)
    marks = [float(x) for x in a.marks.split(',') if x.strip()]
    print(f'合成 {a.duration}s @ {bpm}BPM  style={a.style}  marks={marks} …')
    if a.style == 'vibe':
        L, R = build_vibe(a.duration, bpm, a.seed, marks)
    else:
        L, R = build(a.duration, bpm, a.seed)
    write_wav(a.out, L, R)
    print(f'[ok] {a.out}  ({len(L)/SR:.2f}s, 立体声, 44.1kHz)')
