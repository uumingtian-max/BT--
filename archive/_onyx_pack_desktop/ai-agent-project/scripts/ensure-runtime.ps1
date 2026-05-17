# 启动前轻量补丁（不跑 pytest）
$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backend = Join-Path $root "backend"
$py = "$env:USERPROFILE\miniconda3\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

if (-not $env:PLAYWRIGHT_BROWSERS_PATH) {
    $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:LOCALAPPDATA "ms-playwright"
}
$envFile = Join-Path $backend ".env"
$example = Join-Path $backend ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $example)) {
    Copy-Item $example $envFile
}
if (-not (Test-Path (Join-Path $root "electron\icon-1024.png"))) {
    & $py (Join-Path $root "scripts\build-branding.py") 2>$null
}
