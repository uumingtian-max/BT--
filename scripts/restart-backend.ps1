# 结束 8000 端口旧后端并启动当前仓库最新代码（以 /meta/tools/registry 为就绪探针）
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Backend = Join-Path $Root "backend"
$Logs = Join-Path $Root "logs"
$resolve = Join-Path $Root "scripts\resolve-python.cjs"
$Python = (& node $resolve 2>$null).Trim()
if (-not (Test-Path $Python)) { $Python = "python" }

New-Item -ItemType Directory -Force -Path $Logs | Out-Null

Write-Host "`n=== 重启黑光后端 (port 8000) ===" -ForegroundColor Cyan

Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object {
    Write-Host "  结束 PID $($_.OwningProcess)" -ForegroundColor Yellow
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
  }
Start-Sleep -Seconds 2

$out = Join-Path $Logs "backend.out.log"
$err = Join-Path $Logs "backend.err.log"
$cmd = "cd /d `"$Backend`" & `"$Python`" -m uvicorn main:app --host 127.0.0.1 --port 8000 1>> `"$out`" 2>> `"$err`""
Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", $cmd) -WindowStyle Hidden

for ($i = 0; $i -lt 40; $i++) {
  try {
    $h = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 2
    if ($h.status -eq "ok") { break }
  } catch { Start-Sleep -Milliseconds 500; continue }
  Start-Sleep -Milliseconds 500
}

try {
  $reg = Invoke-RestMethod "http://127.0.0.1:8000/meta/tools/registry" -TimeoutSec 5
  if ($reg.ok -ne $true) { throw "registry ok=false" }
  Write-Host "  /health OK" -ForegroundColor Green
  Write-Host "  /meta/tools/registry -> ok count=$($reg.count)" -ForegroundColor Green
} catch {
  Write-Host "  [WARN] /meta/tools/registry 仍不可用: $($_.Exception.Message)" -ForegroundColor Red
  Write-Host "  查看 logs\backend.err.log" -ForegroundColor Yellow
  exit 1
}

Write-Host "`n后端已就绪: http://127.0.0.1:8000/docs`n" -ForegroundColor Green
