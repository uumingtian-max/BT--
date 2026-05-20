# 预热并 pin 全部常驻模型（keep_alive=24h）
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$resolve = Join-Path $Root "scripts\resolve-python.cjs"
$Python = (& node $resolve 2>$null).Trim()
if (-not (Test-Path $Python)) { $Python = "python" }

Write-Host "[pin-ollama] 预热常驻模型（keep_alive 来自 backend\.env，主脑最后加载）" -ForegroundColor Cyan
& $Python (Join-Path $Root "scripts\pin-ollama-warm.py")

Write-Host "`n查看当前加载: ollama ps" -ForegroundColor DarkGray
ollama ps 2>$null
