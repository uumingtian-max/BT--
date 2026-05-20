# 黑光发版冒烟：默认本地快速评测，生成 outputs/agent_eval_report.md
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$resolve = Join-Path $Root "scripts\resolve-python.cjs"
if (-not (Test-Path $resolve)) {
    Write-Error "找不到 resolve-python.cjs"
}
$Python = (& node $resolve 2>$null).Trim()
if (-not $Python -or -not (Test-Path $Python)) {
    $Python = "python"
}

$argsList = @("$Root\scripts\agent_smoke_suite.py")
if ($env:AGENT_SMOKE_API -eq "1") { $argsList += "--api" }
if ($env:AGENT_SMOKE_QUICK -eq "1") { $argsList += "--quick" }
$argsList += $args

Write-Host "[run-agent-smoke] $Python $($argsList -join ' ')" -ForegroundColor Cyan
& $Python @argsList
exit $LASTEXITCODE
