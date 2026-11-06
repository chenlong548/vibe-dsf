# =====================================================================
# run_all.ps1 —— 一键流水线：渲染 → QA 闸门 → BGM → 音效/旁白 → 混音 → 合成 → 报告
#
#   解决的问题：以前 5 条命令人肉跑、闸门靠自觉。
#   film-love-math 7.14 分（低于 8 分线）照样出了片——这条流水线会让它停在 QA。
#
# 用法（在项目目录里跑，或用 -Project 指定）：
#   powershell -File ..\..\pipeline\run_all.ps1 -Duration 26                 # 全片
#   powershell -File ..\..\pipeline\run_all.ps1 -Start 12 -End 18            # 只重渲一段
#   powershell -File ..\..\pipeline\run_all.ps1 -Duration 11.43 -BgmStyle vibe -Bpm 126   # SCENE-PLAN 带 narration 时自动加旁白
#   powershell -File ..\..\pipeline\run_all.ps1 -SkipRender                  # 只做 QA+BGM+旁白+合成
#   powershell -File ..\..\pipeline\run_all.ps1 -NoGate                      # QA 只出报告不拦截
#
# 退出码：0 成功 / 1 渲染失败 / 2 QA 闸门拦截 / 3 BGM 或合成失败 / 4 音效/旁白/混音失败
# =====================================================================
param(
  [string]$Project  = ".",
  [string]$Html     = "index.html",
  [string]$Frames   = "frames",
  [string]$Plan     = "SCENE-PLAN.json",   # 存在且带 narration 数组时启用旁白阶段
  [double]$Duration = 0,
  [double]$Start    = -1,
  [double]$End      = -1,
  [int]$Fps         = 30,
  [double]$Bpm      = 0,              # 0 = 用 synth_bgm 的风格默认值
  [string]$BgmMarks = "",             # 逗号分隔秒值（场景切换/揭晓拍点），空 = synth_bgm 默认
  [string]$BgmStyle = "ambient",      # ambient（纪录片 77）| vibe（电子 96）
  [string]$Bgm      = "bgm.wav",
  [string]$NarrOut  = "narration.wav",
  [string]$MixOut   = "final_audio.wav",
  [string]$VoiceRate = "+15%",        # TTS 全局语速（plan 单句可覆盖）
  [string]$Out      = "final.mp4",
  [switch]$SkipRender,
  [switch]$SkipBgm,
  [switch]$NoGate
)

# 注意：不能用 "Stop"。PS 5.1 会把原生命令(node/python)的 stderr 输出当成终止错误；
# 我们靠 $LASTEXITCODE 逐段判断成败。
$ErrorActionPreference = "Continue"
$pipeline = $PSScriptRoot
$project  = (Resolve-Path $Project).Path

# ---------- 工具定位：node / python（含 WorkBuddy 托管运行时的回退） ----------
function Resolve-Tool([string]$exe, [string[]]$fallbacks) {
  $got = Get-Command $exe -ErrorAction SilentlyContinue
  if ($got) { return $got.Source }
  foreach ($p in $fallbacks) { if (Test-Path $p) { return $p } }
  return $null
}

$node = Resolve-Tool "node" @(
  "C:\Users\17415\.workbuddy\binaries\node\versions\22.22.2-6\node.exe"
  "C:\Program Files\nodejs\node.exe"
)
$python = $env:PYTHON
if (-not $python -or -not (Test-Path $python)) {
  $python = Resolve-Tool "python" @(
    "C:\Users\17415\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
    "C:\Users\17415\.workbuddy\binaries\python\versions\3.13.12\python.exe"
    "C:\Python314\python.exe"
  )
}
if (-not $node)   { Write-Host "[X]找不到 node"   -ForegroundColor Red; exit 1 }
if (-not $python) { Write-Host "[X]找不到 python（需要 pillow + numpy）" -ForegroundColor Red; exit 1 }

# ---------- ffmpeg 定位：PATH → DSH_FFMPEG_PATH → imageio-ffmpeg → ffmpeg-static ----------
$ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ffmpeg -and $env:DSH_FFMPEG_PATH -and (Test-Path $env:DSH_FFMPEG_PATH)) { $ffmpeg = $env:DSH_FFMPEG_PATH }
if (-not $ffmpeg) {
  try { $ff = & $python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())" 2>$null
        if ($ff -and (Test-Path $ff)) { $ffmpeg = $ff } } catch { }
}
if (-not $ffmpeg) {
  $static = Get-ChildItem "C:\Users\17415\.workbuddy\binaries\node\workspace\node_modules\ffmpeg-static\ffmpeg.exe" -ErrorAction SilentlyContinue
  if ($static) { $ffmpeg = $static.FullName }
}
if ($ffmpeg) {
  # 注入 PATH，让嵌套调用的 build.ps1 / 子进程也能找到
  $env:PATH = "$(Split-Path $ffmpeg);$env:PATH"
  $env:DSH_FFMPEG_PATH = $ffmpeg
  Write-Host "    ffmpeg：$ffmpeg" -ForegroundColor DarkGray
} else {
  Write-Host "[X]找不到 ffmpeg（装法：python -m pip install imageio-ffmpeg 或 winget install Gyan.FFmpeg）" -ForegroundColor Red
  exit 1
}

if (-not (Test-Path (Join-Path $project $Html))) {
  Write-Host "[X]找不到 $Html（目录：$project）" -ForegroundColor Red; exit 1
}

$framesDir = Join-Path $project $Frames
Write-Host "=== 流水线开始：$project ===" -ForegroundColor Cyan
$sw = [System.Diagnostics.Stopwatch]::StartNew()

# ---------- 1. 渲染 ----------
if (-not $SkipRender) {
  Write-Host "`n[1/5] 渲染帧…" -ForegroundColor Cyan
  Push-Location $project
  try {
    $renderArgs = @("$pipeline\render\render_frames.mjs", "--html", $Html, "--out", $Frames, "--fps", "$Fps")
    if ($Start -ge 0 -and $End -gt $Start) { $renderArgs += @("--start", "$Start", "--end", "$End") }
    elseif ($Duration -le 0) { Write-Host "[X]全片渲染需要 -Duration（秒）" -ForegroundColor Red; exit 1 }
    else { $renderArgs += @("--duration", "$Duration") }
    & $node @renderArgs
    if ($LASTEXITCODE -ne 0) { Write-Host "[X]渲染失败" -ForegroundColor Red; exit 1 }
  } finally { Pop-Location }
} else {
  Write-Host "`n[1/5] 跳过渲染（-SkipRender）"
}

if (-not (Test-Path $framesDir)) { Write-Host "[X]帧目录不存在：$framesDir" -ForegroundColor Red; exit 1 }
$frameCount = (Get-ChildItem $framesDir -Filter "frame_*.png" -ErrorAction SilentlyContinue).Count
if (-not $frameCount) { Write-Host "[X]帧目录里没有 frame_*.png" -ForegroundColor Red; exit 1 }
$seconds = [math]::Round($frameCount / $Fps, 2)
Write-Host "    帧数 $frameCount（$seconds 秒 @ ${Fps}fps）"

# ---------- 2. QA 闸门 ----------
Write-Host "`n[2/5] QA 验收（11 项）…" -ForegroundColor Cyan
Push-Location $project
try {
  $qaArgs = @("$pipeline\qa\qa_check.py", $Frames, "--fps", "$Fps", "--json", "qa.json")
  if ($NoGate) { $qaArgs += "--no-gate" }
  & $python @qaArgs
  $qaCode = $LASTEXITCODE
} finally { Pop-Location }
if ($qaCode -ne 0) {
  Write-Host "`n[STOP] QA 闸门拦截：总分 < 8。修完 [X] 项后用 -Start/-End 只重渲受影响的那几秒。" -ForegroundColor Red
  Write-Host "   报告：$(Join-Path $project 'qa.json')" -ForegroundColor Red
  exit 2
}

# ---------- 3. BGM ----------
$bgmPath = Join-Path $project $Bgm
if (-not $SkipBgm) {
  Write-Host "`n[3/5] 合成 BGM（style=$BgmStyle）…" -ForegroundColor Cyan
  Push-Location $project
  try {
    $bgmArgs = @("$pipeline\audio\synth_bgm.py", $Bgm, "--style", $BgmStyle, "--duration", "$seconds")
    if ($Bpm -gt 0) { $bgmArgs += @("--bpm", "$Bpm") }
    if ($BgmMarks -ne "") { $bgmArgs += @("--marks", $BgmMarks) }
    & $python @bgmArgs
    if ($LASTEXITCODE -ne 0) { Write-Host "[X]BGM 合成失败" -ForegroundColor Red; exit 3 }
  } finally { Pop-Location }
} else {
  Write-Host "`n[3/5] 跳过 BGM（-SkipBgm）"
}

# ---------- 4. SFX（plan 带 sfx 时）+ 旁白（plan 带 narration 时）+ 闪避混音 ----------
$narrPath = Join-Path $project $NarrOut
$sfxPath  = Join-Path $project "sfx.wav"
$mixPath  = Join-Path $project $MixOut
$planPath = Join-Path $project $Plan
$hasNarr  = $false
$hasSfx   = $false
$needMix  = $false
if (Test-Path $planPath) {
  $probe = & $python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); print(('yes' if d.get('narration') else 'no'), ('yes' if any(sc.get('sfx') for sc in d.get('scenes',[])) else 'no'))" $planPath 2>$null
  $parts = ("$probe".Trim()) -split '\s+'
  if ($parts.Count -ge 1 -and $parts[0] -eq "yes") { $hasNarr = $true }
  if ($parts.Count -ge 2 -and $parts[1] -eq "yes") { $hasSfx = $true }
}
if ($hasNarr -or $hasSfx) {
  Write-Host "`n[4/5] 音效/旁白 + 闪避混音…" -ForegroundColor Cyan
  Push-Location $project
  try {
    if ($hasSfx) {
      & $python "$pipeline\audio\synth_sfx.py" $sfxPath --plan $Plan --duration $seconds
      if ($LASTEXITCODE -ne 0) { Write-Host "[X]音效合成失败" -ForegroundColor Red; exit 4 }
      $needMix = $true
    }
    if ($hasNarr) {
      & $python "$pipeline\audio\narrate\build_narration.py" $Plan --out $NarrOut --rate $VoiceRate
      if ($LASTEXITCODE -ne 0) { Write-Host "[X]旁白合成失败" -ForegroundColor Red; exit 4 }
      $needMix = $true
    }
    if ($needMix) {
      $mixArgs = @("$pipeline\audio\narrate\mix_audio.py", "--duration", "$seconds", "--out", $MixOut)
      if ($hasNarr -and (Test-Path $narrPath)) { $mixArgs += @("--narration", $NarrOut) }
      if ($hasSfx -and (Test-Path $sfxPath))  { $mixArgs += @("--sfx", "sfx.wav") }
      if ((Test-Path $bgmPath) -and -not $SkipBgm) { $mixArgs += @("--bgm", $Bgm) }
      & $python @mixArgs
      if ($LASTEXITCODE -ne 0) { Write-Host "[X]混音失败" -ForegroundColor Red; exit 4 }
    }
  } finally { Pop-Location }
} else {
  Write-Host "`n[4/5] 跳过音效/旁白（无 $Plan 或 plan 不带 narration/sfx）"
}

# ---------- 5. 合成 ----------
Write-Host "`n[5/5] ffmpeg 合成…" -ForegroundColor Cyan
$buildArgs = @{ Frames = $framesDir; Fps = $Fps; Out = (Join-Path $project $Out) }
if ($needMix -and (Test-Path $mixPath)) { $buildArgs.Audio = $mixPath }
elseif ((Test-Path $bgmPath) -and -not $SkipBgm) { $buildArgs.Audio = $bgmPath }
& powershell -NoProfile -File "$pipeline\compose\build.ps1" @buildArgs
if ($LASTEXITCODE -ne 0) { Write-Host "[X]合成失败" -ForegroundColor Red; exit 3 }

$sw.Stop()
Write-Host "`n=== 完成 ===" -ForegroundColor Green
Write-Host "  成片：$(Join-Path $project $Out)"
Write-Host "  验收：$(Join-Path $project 'qa.json')"
Write-Host ("  总耗时：{0:mm\:ss}" -f $sw.Elapsed)
exit 0
