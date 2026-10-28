# =====================================================================
# build.ps1 —— 把 frames/ 里的 PNG 序列 + 音频合成成片（Windows）
#   用法：
#     powershell -File build.ps1                        # 无音频
#     powershell -File build.ps1 -Audio bgm.wav         # 带音乐
#     powershell -File build.ps1 -Fps 60 -Out v2.mp4
#   需要 ffmpeg：winget install --id Gyan.FFmpeg -e
# =====================================================================
param(
  [string]$Frames = "frames",
  [string]$Audio  = "",
  [int]$Fps       = 30,
  [string]$Out    = "final.mp4",
  [int]$Crf       = 18
)

$ErrorActionPreference = "Stop"

# ffmpeg 解析：PATH → DSH_FFMPEG_PATH（setup.ps1 / run_all.ps1 导出）。
# 注意 imageio-ffmpeg 的二进制名带版本号（ffmpeg-win-x86_64-v7.1.exe），
# 不能依赖 "ffmpeg.exe" 这个名字做匹配，必须直接用完整路径执行。
$ff = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ff -and $env:DSH_FFMPEG_PATH -and (Test-Path $env:DSH_FFMPEG_PATH)) {
  $ff = $env:DSH_FFMPEG_PATH
}
if (-not $ff) {
  Write-Host "✗ 找不到 ffmpeg。先装：winget install --id Gyan.FFmpeg -e" -ForegroundColor Red
  exit 1
}
if (-not (Test-Path $Frames)) { Write-Host "✗ 帧目录不存在：$Frames" -ForegroundColor Red; exit 1 }

$count = (Get-ChildItem $Frames -Filter "frame_*.png").Count
Write-Host "帧数：$count  ($([math]::Round($count / $Fps, 2)) 秒 @ ${Fps}fps)" -ForegroundColor Cyan

$common = @(
  "-y", "-hide_banner",
  "-framerate", "$Fps",
  "-i", "$Frames\frame_%05d.png"
)

if ($Audio -and (Test-Path $Audio)) {
  Write-Host "音轨：$Audio（响度标准化到 -14 LUFS）" -ForegroundColor Cyan
  $args2 = $common + @(
    "-i", $Audio,
    "-c:v", "libx264", "-preset", "slow", "-crf", "$Crf",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
    "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
    "-shortest",
    $Out
  )
  & $ff @args2
} else {
  $args2 = $common + @(
    "-c:v", "libx264", "-preset", "slow", "-crf", "$Crf",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
    $Out
  )
  & $ff @args2
}

if ($LASTEXITCODE -ne 0) { Write-Host "✗ ffmpeg 失败" -ForegroundColor Red; exit 1 }
Write-Host "✓ 成片：$((Resolve-Path $Out).Path)" -ForegroundColor Green
exit 0
