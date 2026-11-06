#!/usr/bin/env bash
# =====================================================================
# build.sh —— 把 frames/ 里的 PNG 序列 + 音频合成成片（macOS / Linux）
#   bash ../pipeline/compose/build.sh                # 无音频
#   bash ../pipeline/compose/build.sh bgm.wav        # 带音乐
#   需要 ffmpeg：brew install ffmpeg / apt install ffmpeg
# =====================================================================
set -euo pipefail

FRAMES="${FRAMES:-frames}"
AUDIO="${1:-}"
FPS="${FPS:-30}"
OUT="${OUT:-final.mp4}"
CRF="${CRF:-18}"

command -v ffmpeg >/dev/null || { echo "✗ 找不到 ffmpeg"; exit 1; }
[ -d "$FRAMES" ] || { echo "✗ 帧目录不存在：$FRAMES"; exit 1; }

COUNT=$(ls "$FRAMES"/frame_*.png | wc -l | tr -d ' ')
echo "帧数：$COUNT（$(echo "scale=2; $COUNT/$FPS" | bc) 秒 @ ${FPS}fps）"

if [ -n "$AUDIO" ] && [ -f "$AUDIO" ]; then
  ffmpeg -y -hide_banner -framerate "$FPS" -i "$FRAMES/frame_%05d.png" -i "$AUDIO" \
    -c:v libx264 -preset slow -crf "$CRF" -pix_fmt yuv420p -movflags +faststart \
    -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 44100 -shortest "$OUT"
else
  ffmpeg -y -hide_banner -framerate "$FPS" -i "$FRAMES/frame_%05d.png" \
    -c:v libx264 -preset slow -crf "$CRF" -pix_fmt yuv420p -movflags +faststart "$OUT"
fi

echo "✓ 成片：$OUT"
