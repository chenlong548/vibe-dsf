# =====================================================================
# setup.ps1 —— 一条命令体检 / 补齐视频生态（Windows）
#
#   powershell -File scripts\setup.ps1                  # 只体检，不动系统
#   powershell -File scripts\setup.ps1 -InstallDeps     # 装 python 依赖
#   powershell -File scripts\setup.ps1 -InstallPlugins  # 装 DSH 视频插件（可选增强）
#   powershell -File scripts\setup.ps1 -All             # 全上
# =====================================================================
param(
  [switch]$InstallDeps,
  [switch]$InstallPlugins,
  [switch]$All
)
if ($All) { $InstallDeps = $true; $InstallPlugins = $true }
$ErrorActionPreference = "Continue"
$ok = 0; $warn = 0

function Check($name, $found, $detail, $hint) {
  if ($found) { Write-Host ("  [OK]   {0,-22} {1}" -f $name, $detail) -ForegroundColor Green; $script:ok++ }
  else        { Write-Host ("  [MISS] {0,-22} {1}" -f $name, $detail) -ForegroundColor Yellow
                Write-Host ("         -> {0}" -f $hint) -ForegroundColor DarkGray; $script:warn++ }
}

Write-Host "`n=== 1. 运行时体检 ===" -ForegroundColor Cyan

$node = Get-Command node -ErrorAction SilentlyContinue
$nodeV = if ($node) { (node -v) } else { "" }
Check "Node.js (>=18)" $node $nodeV "https://nodejs.org/"

$py = Get-Command python -ErrorAction SilentlyContinue
$pyV = if ($py) { (python -V 2>&1) } else { "" }
Check "Python (>=3.10)" $py $pyV "https://www.python.org/"

$chrome = @(
  "C:\Program Files\Google\Chrome\Application\chrome.exe",
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
  "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
Check "Google Chrome" $chrome $(if ($chrome) { $chrome } else { "" }) "https://www.google.com/chrome/"

# ffmpeg：PATH 里没有就找 imageio-ffmpeg 自带的那份
$ff = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ff) {
  try {
    $ff = python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())" 2>$null
    if ($ff -and -not (Test-Path $ff)) { $ff = $null }
  } catch { }
}
Check "ffmpeg" $ff $(if ($ff) { $ff } else { "" }) "png -m pip install imageio-ffmpeg   或   winget install Gyan.FFmpeg"

if ($ff) { $env:DSH_FFMPEG_PATH = $ff; Write-Host "   (已导出 `$env:DSH_FFMPEG_PATH)" -ForegroundColor DarkGray }

$pil = $false
try { python -c "import PIL, numpy" 2>$null; $pil = $true } catch { }
Check "python 依赖 (PIL/numpy)" $pil "" "python -m pip install -r pipeline\requirements.txt"

Write-Host "`n=== 2. 生态文件体检 ===" -ForegroundColor Cyan
$root = Split-Path -Parent $PSScriptRoot
$files = @(
  "pipeline\run_all.ps1", "pipeline\palette.json",
  "pipeline\render\render_frames.mjs", "pipeline\qa\qa_check.py", "pipeline\qa\test_edge_v4.py",
  "pipeline\report\generate.py", "pipeline\report\test_generate.py",
  "pipeline\audio\synth_bgm.py", "pipeline\audio\synth_sfx.py", "pipeline\audio\wave_png.py",
  "pipeline\audio\narrate\build_narration.py", "pipeline\compose\build.ps1",
  "pipeline\blocks\registry.json", "pipeline\scene_writer\build_html.mjs",
  "skills\vibe-film-ds\SKILL.md",
  "skills\vibe-film-ds\references\ds-failure-modes.md",
  "docs\03-FLASH-PLAYBOOK.md", "docs\18-BRAND.md", "docs\20-QA-V4.md", "docs\21-PIPELINE-REPORT.md",
  "docs\22-COMMERCIAL.md", "docs\23-RELEASE.md", "SECURITY.md", "CODE_OF_CONDUCT.md",
  "brand\logo.svg", "brand\BRAND.md", "site\index.html", "site\check.py",
  "styles\paper-gold.md", "styles\nocturne.md", "styles\fable.md", "styles\romance.md",
  "projects\demo-hook-entropy\index.html"
)
foreach ($f in $files) {
  $p = Join-Path $root $f
  Check $f (Test-Path $p) "" "文件缺失，重新解压生态包"
}

Write-Host "`n=== 3. DSH 插件：本生态主张「一个都不装」===" -ForegroundColor Cyan
Write-Host "  hyperframes / remotion / ffmpeg / modlens 全部拒绝（理由见 README 第二节）" -ForegroundColor DarkGray
Write-Host "  核心原因：多一条渲染路径 = flash 多一次走错的机会，而且它不会告诉你。" -ForegroundColor DarkGray
if ($InstallPlugins) {
  Write-Host "`n  你（或某个脚本）传了 -InstallPlugins，但本生态已改为零插件。" -ForegroundColor Yellow
  Write-Host "  若确有需要（例如要做 React/3D 视频），请手动执行：" -ForegroundColor Yellow
  Write-Host "    dsh plugin --profile web add dsh-remotion" -ForegroundColor White
  Write-Host "  并另建项目，不要混进本流水线。" -ForegroundColor Yellow
}

if ($InstallDeps) {
  Write-Host "`n=== 4. 安装 python 依赖 ===" -ForegroundColor Cyan
  python -m pip install -r (Join-Path $root "pipeline\requirements.txt")
  if (-not $ff) {
    Write-Host "  顺手装一个 ffmpeg 二进制 …" -ForegroundColor Cyan
    python -m pip install imageio-ffmpeg
  }
}

Write-Host "`n=== 体检结果 ===" -ForegroundColor Cyan
Write-Host ("  通过 {0} 项 / 缺失 {1} 项" -f $ok, $warn) -ForegroundColor $(if ($warn -eq 0) { "Green" } else { "Yellow" })
if ($warn -eq 0) {
  Write-Host "  全部就绪。下一步：" -ForegroundColor Green
  Write-Host "    cd projects\demo-26s" -ForegroundColor White
  Write-Host "    node ..\..\pipeline\render_frames.mjs --stills 3,45,132" -ForegroundColor White
} else {
  Write-Host "  按上面 [MISS] 的提示补齐后重跑本脚本。" -ForegroundColor Yellow
}
Write-Host ""
