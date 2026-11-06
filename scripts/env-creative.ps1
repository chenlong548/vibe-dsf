# =====================================================================
# env-creative.ps1 —— 创意模式：云雾 API + Claude Opus 5.5（P1 #8 模型分工）
#   用法：. .\scripts\env-creative.ps1   然后在本目录跑 claude
#   定位：只干"定调"活——风格定义 / 创意帧抽卡 / 复杂积木首版。
#         批量场景、局部修补、QA 修复循环 → 回 env.ps1（flash，¥3-5/片）。
#   注意：key 自己填，不要提交到仓库；模型 ID 以云雾控制台分组列表为准
# =====================================================================

# ---- 云雾端点（2026-11 实测，旧 yunwu.ai / api.yunwu.cloud 已停用迁移）----
# 新站（新注册用户）：https://v2.cloudmist.cloud   老站（老用户）：https://api.cloudmist.cloud
# ⚠️ 两站账号独立、Key 不通用——按你注册的站点二选一，填错报「无效的令牌」
# Claude Code 的 BASE_URL 不带 /v1（请求路径本身就是 /v1/messages）
$env:ANTHROPIC_BASE_URL   = "https://v2.cloudmist.cloud"
$env:ANTHROPIC_AUTH_TOKEN = "<在这里填你的云雾 API Key，sk- 开头>"
$env:API_TIMEOUT_MS       = "300000"                    # Opus 自适应思考较慢，超时 5 分钟

# ---- 四个模型位，全部锁成 opus-5-5（不给悄悄降级留余地）----
$env:ANTHROPIC_MODEL                 = "claude-opus-5-5"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL    = "claude-opus-5-5"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL  = "claude-opus-5-5"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL   = "claude-opus-5-5"
$env:CLAUDE_CODE_SUBAGENT_MODEL      = "claude-opus-5-5"

# ---- 创意模式参数：思考拉满（Opus 5.5 自适应思考常开，effort 控制深度 low→max）----
$env:CLAUDE_CODE_EFFORT_LEVEL        = "max"
$env:CLAUDE_CODE_AUTO_COMPACT_WINDOW = "786432"

Write-Host "创意模式已切换：云雾 + claude-opus-5-5" -ForegroundColor Green
Write-Host "  BASE_URL = $env:ANTHROPIC_BASE_URL"
Write-Host "  MODEL    = $env:ANTHROPIC_MODEL  (1M ctx / 128K out / 自适应思考常开)"
Write-Host "  effort   = $env:CLAUDE_CODE_EFFORT_LEVEL   timeout = $($env:API_TIMEOUT_MS)ms"
Write-Host ""
Write-Host "本会话只干定调活：风格定义 / 创意帧抽卡 / 复杂积木首版" -ForegroundColor Yellow
Write-Host "批量场景 / 局部修补 / QA 循环 → 换回 . .\scripts\env.ps1（flash，成本 ¥3-5/片）" -ForegroundColor DarkGray
Write-Host "开工前先读：docs/01-MODEL-PROFILE.md 第 7 节（分工契约）" -ForegroundColor Cyan
