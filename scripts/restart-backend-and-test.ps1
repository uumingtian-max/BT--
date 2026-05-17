# 重启 FastAPI 后端（8000）并实测 /agent/run（需 vLLM 等网关已按 backend/.env 就绪）
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $root 'backend'
$logDir = Join-Path $root 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

Write-Host "=== 释放 8000 端口 ===" -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object {
        if ($_ -and $_ -gt 0) {
            Write-Host "Stopping PID $_"
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    }
Start-Sleep -Seconds 2

$py = 'python'
if (Test-Path "$env:USERPROFILE\miniconda3\python.exe") {
    $py = "$env:USERPROFILE\miniconda3\python.exe"
}

$stdout = Join-Path $logDir 'uvicorn-restart-test.out.log'
$stderr = Join-Path $logDir 'uvicorn-restart-test.err.log'
if (Test-Path $stdout) { Remove-Item $stdout -Force }
if (Test-Path $stderr) { Remove-Item $stderr -Force }

Write-Host "=== 启动 uvicorn ===" -ForegroundColor Cyan
$proc = Start-Process -FilePath $py `
    -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000') `
    -WorkingDirectory $backend -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $stdout -RedirectStandardError $stderr

Write-Host "=== 等待 /health (PID $($proc.Id)) ===" -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    try {
        $h = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2
        if ($h.StatusCode -eq 200) { $ok = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 500
}
if (-not $ok) {
    Write-Host '后端未就绪。stderr 尾部：' -ForegroundColor Red
    if (Test-Path $stderr) { Get-Content $stderr -Tail 30 }
    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch { }
    exit 1
}
Write-Host 'health OK' -ForegroundColor Green

Write-Host "=== GET /agent/config ===" -ForegroundColor Cyan
$cfg = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/agent/config' -TimeoutSec 15
$cfg | ConvertTo-Json -Depth 5

Write-Host "=== POST /agent/run (SSE) ===" -ForegroundColor Cyan
$model = [string]$cfg.default_model
$body = (@{ message = '只回复一个词：PONG'; model = $model } | ConvertTo-Json -Compress)
$tmp = Join-Path $env:TEMP ("agent-run-{0}.json" -f [Guid]::NewGuid().ToString('n'))
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($tmp, $body, $utf8)
try {
    curl.exe -sS -N --max-time 120 -X POST 'http://127.0.0.1:8000/agent/run' `
        -H 'Content-Type: application/json' `
        -H 'Accept: text/event-stream' `
        --data-binary "@$tmp"
} finally {
    Remove-Item -Force $tmp -ErrorAction SilentlyContinue
}

Write-Host "`n=== 停止测试用 uvicorn ===" -ForegroundColor Cyan
try {
    Stop-Process -Id $proc.Id -Force -ErrorAction Stop
} catch {
    Write-Host $_.Exception.Message
}
Write-Host '完成。若正在用 Electron 打开 ONYX，请关掉后重开一次以连上本机后端（或保持仅用本脚本起的 8000）。' -ForegroundColor Green
