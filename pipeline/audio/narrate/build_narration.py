#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_narration.py — SCENE-PLAN.narration → 全片对齐旁白轨 narration.wav
- 逐句 TTS（provider=tts_edge，可替换）
- 窗口拟合：句长 > (t_out-t_in) 时 atempo 压速（上限 1.25，超过只警告不截断）
- 按 t_in 铺入全片长度静音底轨（44.1k mono s16）
用法：
  python build_narration.py <SCENE-PLAN.json> --out narration.wav
  [--voice zh-CN-YunxiNeural] [--rate +8%]
"""
import argparse
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tts_edge import synthesize, _ffmpeg, SR, wav_duration  # noqa: E402

ATEMPO_MAX = 1.25


def to_float(path):
    with wave.open(path, "rb") as w:
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def atempo(src, factor, out):
    subprocess.run(
        [_ffmpeg(), "-y", "-loglevel", "error", "-i", src,
         "-filter:a", f"atempo={factor:.4f}",
         "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", out],
        check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--out", default="narration.wav")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--rate", default=None)
    a = ap.parse_args()

    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    narr = plan.get("narration") or []
    meta = plan.get("meta", {})
    dur = float(meta.get("duration", 0))
    if not narr:
        print(json.dumps({"ok": False, "errors": ["plan 里没有 narration 数组"]}, ensure_ascii=False))
        return 2
    if dur <= 0:
        print(json.dumps({"ok": False, "errors": ["meta.duration 非法"]}, ensure_ascii=False))
        return 2

    total = int(round(dur * SR))
    master = np.zeros(total, dtype=np.float32)
    tmp = Path(tempfile.mkdtemp(prefix="narr_"))
    items, warnings = [], []

    for i, item in enumerate(narr):
        text = str(item.get("text", "")).strip()
        t_in = float(item["t_in"])
        t_out = float(item["t_out"])
        voice = item.get("voice") or a.voice or __import__("tts_edge").DEFAULT_VOICE
        rate = item.get("rate") or a.rate or __import__("tts_edge").DEFAULT_RATE
        need = t_out - t_in

        raw = tmp / f"n{i}.wav"
        d_raw = synthesize(text, str(raw), voice, rate)

        at = max(1.0, min(d_raw / need, ATEMPO_MAX)) if need > 0 else 1.0
        if at > 1.001:
            fixed = tmp / f"n{i}f.wav"
            atempo(str(raw), at, str(fixed))
            src = fixed
        else:
            src = raw
        d = wav_duration(str(src))

        clip = to_float(str(src))
        start = int(round(t_in * SR))
        room = total - start
        cut = min(len(clip), room)
        master[start:start + cut] += clip[:cut]

        entry = {"i": i, "t_in": t_in, "need": round(need, 3), "raw": round(d_raw, 3),
                 "atempo": round(at, 3), "final": round(d, 3), "text": text[:24]}
        if d > need + 0.05:
            entry["fit"] = "over"
            warnings.append(f"n{i} 压速后仍超窗 {d:.2f}s > {need:.2f}s（检查是否与下一句重叠/截尾）")
        elif at > 1.001:
            entry["fit"] = "tempo"
        else:
            entry["fit"] = "natural"
        if cut < len(clip):
            entry["truncated"] = True
            warnings.append(f"n{i} 尾部被总时长截掉 {len(clip) - cut} 帧")
        items.append(entry)

    peak = float(np.max(np.abs(master))) if total else 0.0
    if peak > 0.99:
        master *= 0.99 / peak
        warnings.append(f"峰值 {peak:.2f} 触顶，已整体降 0.99/{peak:.2f}")

    with wave.open(a.out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(master, -1, 1) * 32767).astype(np.int16).tobytes())

    print(json.dumps({"ok": True, "out": a.out, "duration": dur, "sr": SR,
                      "voice_items": items, "warnings": warnings},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
