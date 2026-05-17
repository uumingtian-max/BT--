# 实测 vLLM OpenAI 兼容 API：/v1/models + /v1/chat/completions
# 用法（在项目根或任意目录）:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-vllm-live.ps1
#   powershell ... -File scripts\test-vllm-live.ps1 -BaseUrl http://127.0.0.1:8001/v1 -Model ''

param(
    [string]$BaseUrl = 'http://127.0.0.1:8001/v1',
    [string]$ApiKey = 'local',
    [string]$Model = '',
    [int]$MaxTokens = 64,
    [int]$TimeoutSec = 180
)

$ErrorActionPreference = 'Stop'
$base = $BaseUrl.TrimEnd('/')

Write-Host "=== TCP ===" -ForegroundColor Cyan
$probeRoot = ($base -replace '/v1/?$', '').TrimEnd('/')
try {
    $uri = [System.Uri]$probeRoot
    $t = Test-NetConnection -ComputerName $uri.Host -Port $uri.Port -WarningAction SilentlyContinue
    Write-Host ("Target {0}:{1}" -f $uri.Host, $uri.Port)
    if ($t.TcpTestSucceeded) { Write-Host "  TcpTestSucceeded: true" -ForegroundColor Green }
    else { Write-Host "  TcpTestSucceeded: false — 请先启动 vLLM（或检查端口/防火墙）" -ForegroundColor Yellow }
} catch {
    Write-Host "  (skip TCP probe)" -ForegroundColor DarkGray
}

Write-Host "`n=== GET $base/models ===" -ForegroundColor Cyan
$headers = @{ Authorization = "Bearer $ApiKey" }
$m = Invoke-RestMethod -Uri "$base/models" -Headers $headers -TimeoutSec $TimeoutSec
$ids = @($m.data | ForEach-Object { $_.id })
if (-not $ids -or $ids.Count -eq 0) { throw 'No models in /v1/models response' }
Write-Host "Models:" ($ids -join ', ')
$useModel = if ($Model) { $Model } else { $ids[0] }
Write-Host "Using model: $useModel" -ForegroundColor Green

Write-Host "`n=== POST $base/chat/completions ===" -ForegroundColor Cyan
$body = @{
    model       = $useModel
    messages    = @(@{ role = 'user'; content = '用一句话回答：1+1等于几？只输出数字。' })
    max_tokens  = $MaxTokens
    temperature = 0.2
    stream      = $false
} | ConvertTo-Json -Depth 6 -Compress

$resp = Invoke-RestMethod -Uri "$base/chat/completions" -Method Post -Headers (@{
        'Content-Type' = 'application/json'
        Authorization  = "Bearer $ApiKey"
}) -Body $body -TimeoutSec $TimeoutSec

$content = $resp.choices[0].message.content
Write-Host "Assistant:" -ForegroundColor Green
Write-Host $content
Write-Host "`nDone (OK)." -ForegroundColor Green
