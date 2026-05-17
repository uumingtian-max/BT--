# 实机全工具演练：启动后端 -> 跑 test-all-tools-live.py -> 输出报告
$ErrorActionPreference = "Stop"
$root = "c:\Users\ROG\Desktop\ai-agent-project"
$py = "$env:USERPROFILE\miniconda3\python.exe"
$logDir = Join-Path $root "logs"

if (-not $env:SKIP_ENSURE_PATCHES) {
    powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\ensure-patches.ps1")
}

if ($env:TOOL_LIVE_START_VLLM -eq "1") {
    powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\ensure-vllm.ps1") -Start -ApplyEnv -WaitSec 600
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

$be = Start-Process -FilePath $py -ArgumentList @(
    "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"
) -WorkingDirectory (Join-Path $root "backend") -WindowStyle Hidden -PassThru

$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    try {
        Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 2 | Out-Null
        $ready = $true
        break
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ready) { throw "后端未启动" }

Write-Host "后端 PID=$($be.Id)" -ForegroundColor Cyan
$env:PLAYWRIGHT_BROWSERS_PATH = "$env:LOCALAPPDATA\ms-playwright"
$env:ENABLE_IMAGE_PLACEHOLDER = "1"

& $py (Join-Path $root "scripts\test-all-tools-live.py")
$code = $LASTEXITCODE

Stop-Process -Id $be.Id -Force -ErrorAction SilentlyContinue
exit $code
