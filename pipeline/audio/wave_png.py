#!/usr/bin/env python3
"""
wave_png.py —— 把 wav 画成波形图（听不见也能验）

为什么需要：agent 听不到声音。BGM 有没有爆音、有没有空段、段落起伏对不对，
只能看图。这张图里能看出：
  · 整体包络（有没有忽大忽小）
  · 拍点网格（BPM 对不对齐）
  · 段落能量（钩子段该弱、推演段该满）
  · 冲击点（marks 的位置有没有"重量"）

用法：
  python ../pipeline/audio/wave_png.py bgm_vibe.wav out.png --bpm 96 --marks 24,48,60
"""
import argparse
import wave
import numpy as np
from PIL import Image, ImageDraw

W, H = 1600, 560
BG = (16, 12, 10)
GRID = (52, 40, 34)
BAR = (214, 160, 96)          # 暖金
PEAK = (245, 214, 160)
MARK = (200, 96, 70)
TEXT = (150, 130, 110)


def load(path):
    with wave.open(path, 'rb') as w:
        ch = w.getnchannels()
        sw = w.getsampwidth()
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        raise SystemExit('只支持 16bit PCM')
    a = np.frombuffer(raw, dtype='<i2').astype(np.float32) / 32768.0
    if ch == 2:
        a = a.reshape(-1, 2).mean(axis=1)
    return a, sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('wav')
    ap.add_argument('out')
    ap.add_argument('--bpm', type=float, default=96)
    ap.add_argument('--marks', type=str, default='')
    a = ap.parse_args()

    x, sr = load(a.wav)
    dur = len(x) / sr
    marks = [float(m) for m in a.marks.split(',') if m.strip()]

    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)

    # 拍点网格
    beat = 60.0 / a.bpm
    bar = beat * 4
    t = 0.0
    while t <= dur:
        px = int(t / dur * W)
        col = GRID if abs((t / bar) % 1) > 1e-6 else (74, 56, 46)
        d.line([(px, 40), (px, H - 40)], fill=col, width=1)
        t += bar

    # 波形（每像素列取 min/max）
    cols = np.linspace(0, len(x), W + 1).astype(int)
    mid = H // 2
    scale = (H / 2 - 60)
    for i in range(W):
        seg = x[cols[i]:max(cols[i] + 1, cols[i + 1])]
        if len(seg) == 0:
            continue
        lo, hi = seg.min(), seg.max()
        d.line([(i, mid - hi * scale), (i, mid - lo * scale)], fill=BAR, width=2)

    # 峰值包络（每 0.5 秒一格，画细线）
    step = int(0.25 * sr)
    for s in range(0, len(x) - step, step):
        pk = np.abs(x[s:s + step]).max()
        px = int(s / len(x) * W)
        d.line([(px, mid - pk * scale), (px, mid + pk * scale)], fill=PEAK, width=1)

    # 冲击点
    for m in marks:
        px = int(m / dur * W)
        d.line([(px, 20), (px, H - 20)], fill=MARK, width=2)
        d.text((px + 5, 22), f'{m:g}s', fill=MARK)

    # 标尺
    d.text((8, 8), f'{a.bpm:g} BPM   {dur:.2f}s', fill=TEXT)
    d.text((8, H - 22), '0s', fill=TEXT)
    d.text((W - 60, H - 22), f'{dur:.0f}s', fill=TEXT)
    img.save(a.out)
    print(f'[ok] {a.out}  {W}x{H}  {dur:.2f}s  marks={marks}')


if __name__ == '__main__':
    main()
