#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_edge.py — 旁白 TTS provider：edge-tts（微软神经音色，零 key、免费）
统一输出契约：44100Hz / mono / s16 wav。
换引擎只需实现同签名 synthesize(text, out_wav, voice=..., rate=...)：
  - tts_cosyvoice.py（本地，需 N 卡 —— 本机实测无 N 卡，挂起待条件）
  - tts_fish.py（Fish Audio API，需 key）
用法：
  库调用：from tts_edge import synthesize
  单句自测：python tts_edge.py "你好世界" out.wav [--voice zh-CN-YunxiNeural] [--rate +8%]
"""
import argparse
import asyncio
import os
import subprocess
import tempfile
import wave

SR = 44100
DEFAULT_VOICE = "zh-CN-YunxiNeural"   # 年轻男声，讲解感强（知识区常用）
DEFAULT_RATE = "+8%"                  # 知识解说普遍微微加速提节奏


def _ffmpeg():
    """四级解析的 python 版：imageio-ffmpeg 优先（本机已装），PATH 兜底。"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def wav_duration(path):
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def wav_frames(path):
    with wave.open(path, "rb") as w:
        return w.readframes(w.getnframes())


async def _save_mp3(text, voice, rate, mp3_path):
    import edge_tts
    com = edge_tts.Communicate(text, voice=voice, rate=rate)
    await com.save(mp3_path)


def synthesize(text, out_wav, voice=DEFAULT_VOICE, rate=DEFAULT_RATE):
    """text → 44.1k mono s16 wav。返回句长秒。"""
    if not text or not text.strip():
        raise ValueError("TTS 文本为空")
    mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    mp3.close()
    try:
        asyncio.run(_save_mp3(text.strip(), voice, rate, mp3.name))
        subprocess.run(
            [_ffmpeg(), "-y", "-loglevel", "error", "-i", mp3.name,
             "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", out_wav],
            check=True)
    finally:
        try:
            os.remove(mp3.name)
        except OSError:
            pass
    return wav_duration(out_wav)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("out")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--rate", default=DEFAULT_RATE)
    a = ap.parse_args()
    d = synthesize(a.text, a.out, a.voice, a.rate)
    print(f"OK {d:.2f}s -> {a.out}  (voice={a.voice}, rate={a.rate})")


if __name__ == "__main__":
    main()
