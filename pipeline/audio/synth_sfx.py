#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synth_sfx.py — 按 SCENE-PLAN 的 sfx 清单合成音效轨（无采样、无版权、确定性）

为什么需要：比特新语式观感的一半来自音效贴着动效走（数字砸下配 impact、
卡片飞入配 whoosh、揭晓前 riser 蓄力）。只有 BGM 的片子"MV 感缺一半"。

时基契约：sfx.t 是**绝对秒**（与场景边界同系），riser 例外——它的 t 是
揭晓点，合成时向前铺（起点 = t - dur），语义是"提前蓄力"。

音效白名单（validate_plan 硬闸第 11 组同源）：
  impact-low  低频砸落（场景切换 / 数字落定）      0.90s  峰 0.22
  impact-mid  中频砸落（卡片/面板落定）            0.60s  峰 0.18
  tick        短促 UI 声（标记点亮 / 计数步进）    0.05s  峰 0.13
  riser       上升噪声（揭晓前蓄力，向前铺 2.0s）  2.00s  峰 0.12
  sub-drop    次低频下坠（反转 / 揭底）            0.80s  峰 0.20
  whoosh      带通噪声横扫（元素飞入 / 转场）      0.55s  峰 0.15

响度设计：单发峰 0.12-0.22 —— 混音 bus 里 BGM 是 0.32 增益、旁白 1.0，
音效要"贴着动效、不抢旁白"。sfx 轨不参与闪避（它本来就该跟着画面走）。

确定性：同一份 plan + 同一个 --seed，永远得到同一个 wav。

用法：
  python ../pipeline/audio/synth_sfx.py sfx.wav --plan SCENE-PLAN.json --duration 23.81
  python ../pipeline/audio/synth_sfx.py sfx.wav --plan SCENE-PLAN.json --duration 23.81 --seed 7
输出 JSON 报告（events / by_name / peak_dbfs）。
"""
import argparse
import json
import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100

# name → (工厂, 时长s, 目标峰, 时基偏移方向)  offset<0 = 向前铺
WHITELIST = ("impact-low", "impact-mid", "tick", "riser", "sub-drop", "whoosh")


def _norm(x, peak):
    m = float(np.max(np.abs(x)))
    return x * (peak / m) if m > 1e-9 else x


def _attack(x, ms=4):
    """起点 ms 短斜坡，防爆音。"""
    k = int(SR * ms / 1000)
    if k > 0 and len(x) > k:
        x[:k] *= np.linspace(0, 1, k)
    return x


def sfx_impact_low(rng):
    """低频砸落：90→38Hz 指数扫频 + tanh 饱和 + 噪声瞬态。"""
    dur = 0.90
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 38 + (90 - 38) * np.exp(-t * 8.0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    boom = np.tanh(np.sin(ph) * np.exp(-t * 5.0) * 1.8) / 1.8
    noise = rng.standard_normal(n) * np.exp(-t * 30) * 0.30
    return _attack(boom + noise)


def sfx_impact_mid(rng):
    """中频砸落：150→70Hz，比 low 快、更"敲"一点。"""
    dur = 0.60
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 70 + (150 - 70) * np.exp(-t * 9.0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.tanh(np.sin(ph) * np.exp(-t * 7.0) * 1.6) / 1.6
    noise = rng.standard_normal(n) * np.exp(-t * 40) * 0.35
    return _attack(body + noise)


def sfx_tick(rng):
    """UI tick：两三个周期的 2.4kHz 纯音 + 极短噪声，像标记点亮。"""
    dur = 0.05
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 90)
    click = rng.standard_normal(n) * np.exp(-t * 220) * 0.25
    return _attack(tone + click, ms=1)


def sfx_riser(rng):
    """上升噪声：一阶低通截止随时间上移（synth_bgm 同款技术）。"""
    dur = 2.00
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    a = 0.02 + 0.85 * (t / dur) ** 2
    y = 0.0
    for i in range(n):  # 纯 python 循环：2s ≈ 88k 点，~0.3s 可接受
        y += a[i] * (noise[i] - y)
        out[i] = y
    return out * (t / dur) ** 2.2


def sfx_sub_drop(rng):
    """次低频下坠：55→24Hz + 轻饱和，"底掉了"的失落感。"""
    dur = 0.80
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 24 + (55 - 24) * np.exp(-t * 3.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.tanh(np.sin(ph) * np.exp(-t * 4.5) * 1.7) / 1.7
    return _attack(x)


def sfx_whoosh(rng):
    """横扫噪声：低通截止 0.04→0.5 上升，减去更低频成分近似带通；菱形包络。"""
    dur = 0.55
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    noise = rng.standard_normal(n)
    a_hi = 0.04 + 0.46 * u
    y_hi = np.zeros(n)
    y_lo = np.zeros(n)
    h = l = 0.0
    for i in range(n):
        h += a_hi[i] * (noise[i] - h)
        l += 0.015 * (noise[i] - l)
        y_hi[i] = h
        y_lo[i] = l
    band = y_hi - y_lo  # 高通部分 = 移动中的"呼"声
    return band * np.sin(np.pi * u) ** 1.5


FACTORY = {
    "impact-low": (sfx_impact_low, 0.90, 0.22, "center"),
    "impact-mid": (sfx_impact_mid, 0.60, 0.18, "center"),
    "tick":       (sfx_tick,       0.05, 0.13, "alternate"),
    "riser":      (sfx_riser,      2.00, 0.12, "alternate"),
    "sub-drop":   (sfx_sub_drop,   0.80, 0.20, "center"),
    "whoosh":     (sfx_whoosh,     0.55, 0.15, "alternate"),
}


def collect_events(plan):
    """plan → [(t, name)]，绝对时基、升序。"""
    ev = []
    for sc in plan.get("scenes", []):
        for s in sc.get("sfx", []):
            ev.append((float(s["t"]), str(s["name"])))
    return sorted(ev)


def build(events, duration, seed, gain=1.0):
    rng = np.random.default_rng(seed)
    total = int(round(duration * SR))
    L = np.zeros(total, dtype=np.float64)
    R = np.zeros(total, dtype=np.float64)
    alt = 0
    by_name = {}
    skipped = []
    for t, name in events:
        if name not in FACTORY:
            skipped.append({"t": t, "name": name, "why": "not in whitelist"})
            continue
        fac, dur, peak, pan_mode = FACTORY[name]
        start = t - dur if name == "riser" else t  # riser 向前铺
        i0 = int(round(start * SR))
        if i0 >= total - int(0.05 * SR) or t < 0.05:
            skipped.append({"t": t, "name": name, "why": "outside timeline"})
            continue
        seg = _norm(fac(rng), peak) * gain
        n = min(len(seg), total - max(i0, 0))
        if n <= 0:
            skipped.append({"t": t, "name": name, "why": "outside timeline"})
            continue
        if i0 < 0:
            seg = seg[-i0:]
            n = len(seg)
            i0 = 0
        if pan_mode == "center":
            gl, gr = 1.0, 1.0
        else:
            gl, gr = (1.0, 0.85) if alt % 2 == 0 else (0.85, 1.0)
            alt += 1
        L[i0:i0 + n] += seg[:n] * gl
        R[i0:i0 + n] += seg[:n] * gr
        by_name[name] = by_name.get(name, 0) + 1

    # 片尾 0.25s 收尾斜坡，防最后一个 impact 被切在半空
    tail = min(int(0.25 * SR), total)
    if tail > 0:
        L[-tail:] *= np.linspace(1, 0, tail)
        R[-tail:] *= np.linspace(1, 0, tail)
    peak = float(np.max(np.abs(L))) if total else 0.0
    return L, R, by_name, skipped, peak


def write_wav(path, L, R):
    data = np.stack([L, R], axis=1)
    pcm = np.clip(data * 32767, -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="输出 wav 路径")
    ap.add_argument("--plan", required=True, help="SCENE-PLAN.json（读 scenes[].sfx）")
    ap.add_argument("--duration", type=float, required=True, help="成片时长（秒）")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--gain", type=float, default=1.0, help="整体增益微调")
    a = ap.parse_args()

    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    events = collect_events(plan)
    if not events:
        print(json.dumps({"ok": False, "errors": ["plan 里没有任何 sfx 事件"]}, ensure_ascii=False))
        return 2

    L, R, by_name, skipped, peak = build(events, a.duration, a.seed, a.gain)
    write_wav(a.out, L, R)
    print(json.dumps({
        "ok": True,
        "out": a.out,
        "duration": a.duration,
        "events": len(events),
        "by_name": by_name,
        "skipped": skipped,
        "peak_dbfs": round(20 * np.log10(max(peak, 1e-6)), 2),
        "seed": a.seed,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
