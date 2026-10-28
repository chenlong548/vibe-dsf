# =====================================================================
# env.ps1 —— 把环境锁死在 flash（不给任何模型映射留余地）
#   用法：. .\scripts\env.ps1     然后 cd 到项目目录跑 claude
#   注意：key 自己填，不要提交到仓库
# =====================================================================

$env:ANTHROPIC_BASE_URL   = "https://api.deepseek.com/anthropic"
$env:ANTHROPIC_AUTH_TOKEN = "<在这里填你的 DeepSeek API Key>"

# ---- 四个模型位，全部锁成 flash ----
# 官方默认映射是 claude-opus* -> v4-pro；你一触发 opus 档就会悄悄换模型，
# 风格和坏习惯全变。这里逐个覆盖，杜绝"我也没注意换了模型"。
$env:ANTHROPIC_MODEL                 = "deepseek-flash[1m]"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL    = "deepseek-flash[1m]"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL  = "deepseek-flash[1m]"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL   = "deepseek-flash"
$env:CLAUDE_CODE_SUBAGENT_MODEL      = "deepseek-flash"

# ---- flash 专用参数 ----
$env:CLAUDE_CODE_EFFORT_LEVEL        = "max"       # 思考拉满（关掉会明显变笨）
$env:CLAUDE_CODE_AUTO_COMPACT_WINDOW = "786432"    # 768K 压缩窗口，避免中途丢分镜表

Write-Host "环境已锁定到 flash：" -ForegroundColor Green
Write-Host "  BASE_URL = $env:ANTHROPIC_BASE_URL"
Write-Host "  MODEL    = $env:ANTHROPIC_MODEL"
Write-Host "  OPUS位   = $env:ANTHROPIC_DEFAULT_OPUS_MODEL  (已覆盖官方默认的 v4-pro 映射)"
Write-Host "  effort   = $env:CLAUDE_CODE_EFFORT_LEVEL"
Write-Host ""
Write-Host "下一步：cd 到项目目录，执行 claude" -ForegroundColor Cyan
Write-Host "开工前先让它读：docs/03-FLASH-PLAYBOOK.md + skills/vibe-film-ds/SKILL.md" -ForegroundColor DarkGray
