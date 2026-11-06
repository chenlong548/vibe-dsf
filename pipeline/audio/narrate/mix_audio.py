#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mix_audio.py — 旁白 + BGM → 成片音轨（旁白侧链自动闪避）
原理：对旁白轨求 50ms RMS 包络 → 平滑（attack 0.12s / release 0.45s）→
      BGM 增益在有人声处压低 --duck-db dB，无人声处回到 --bgm-gain。
确定性：纯 numpy 运算，无随机。
用法：
  python mix_audio.py --narration narration.wav --bgm bgm.wav \
      --duration 9.5238 --out final_audio.wav [--bgm-gain 0.32] [--duck-db 9] [--voice-gain 1.0]
  （narration / bgm 至少给一个；只给 narration 时直接转立体声输出）
"""
import argparse
import json
import wave
from pathlib import Path

import numpy as np

SR = 44100


def load(path):
    with wave.open(path, "rb") as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        raw = w.readframes(n)
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        x = x.reshape(-1, 2).mean(axis=1)
    if sr != SR:  # 线性重采样兜底（正常链路里 provider 已统一 44.1k）
        k = int(round(len(x) * SR / sr))
        x = np.interp(np.linspace(0, len(x) - 1, k), np.arange(len(x)), x)
    return x


def save_stereo(path, mono):
    s = (np.clip(mono, -1, 1) * 32767).astype(np.int16)
    inter = np.empty(s.size * 2, dtype=np.int16)
    inter[0::2] = s
    inter[1::2] = s
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(inter.tobytes())


def duck_envelope(narr, total, duck_db, attack_s=0.12, release_s=0.45):
    """0..1 增益曲线：有人声→duck，无人声→1。one-pole 平滑。"""
    win = int(SR * 0.05)
    if len(narr) < win:
        return np.ones(total)
    rms = np.sqrt(np.convolve(narr ** 2, np.ones(win) / win, mode="same"))
    thr = max(rms.max() * 0.12, 1e-4)
    active = np.clip(rms / thr, 0, 1)
    g = np.ones(total)
    target = 10 ** (-duck_db / 20.0)
    a_att = 1 - np.exp(-1 / (SR * attack_s))
    a_rel = 1 - np.exp(-1 / (SR * release_s))
    cur = 1.0
    n = min(total, len(active))
    for i in range(n):
        want = target if active[i] > 0.25 else 1.0
        cur += (want - cur) * (a_att if want < cur else a_rel)
        g[i] = cur
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narration", default=None)
    ap.add_argument("--bgm", default=None)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--out", default="final_audio.wav")
    ap.add_argument("--bgm-gain", type=float, default=0.32)
    ap.add_argument("--duck-db", type=float, default=9.0)
    ap.add_argument("--voice-gain", type=float, default=1.0)
    a = ap.parse_args()
    if not a.narration and not a.bgm:
        print(json.dumps({"ok": False, "errors": ["--narration / --bgm 至少给一个"]}, ensure_ascii=False))
        return 2

    total = int(round(a.duration * SR))
    narr = load(a.narration)[:total] if a.narration else np.zeros(total)
    if len(narr) < total:
        narr = np.pad(narr, (0, total - len(narr)))

    if a.bgm:
        bgm = load(a.bgm)
        if len(bgm) < total:
            bgm = np.pad(bgm, (0, total - len(bgm)))
        g = duck_envelope(narr, total, a.duck_db)
        bus = bgm[:total] * a.bgm_gain * g + narr[:total] * a.voice_gain
        ducked_pct = float(np.mean(g < 0.85) * 100)
    else:
        bus = narr[:total] * a.voice_gain
        ducked_pct = 0.0

    peak = float(np.max(np.abs(bus))) if total else 0.0
    save_stereo(a.out, bus)
    print(json.dumps({"ok": True, "out": a.out, "duration": a.duration,
                      "peak_dbfs": round(20 * __import__("math").log10(max(peak, 1e-6)), 2),
                      "duck_coverage_pct": round(ducked_pct, 1)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
