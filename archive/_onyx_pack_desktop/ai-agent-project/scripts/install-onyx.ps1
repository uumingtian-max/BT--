# ONYX-OVERRIDE 项目安装（仅在本项目内使用，勿与桌面 Downloads\install.ps1 混用）
# 用法: powershell -ExecutionPolicy Bypass -File scripts\install-onyx.ps1

param(
    [string]$ProjectRoot = "",
    [switch]$SkipPlaywright,
    [switch]$SkipBuild,
    [switch]$NoShortcut
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = if ($ProjectRoot) { (Resolve-Path $ProjectRoot).Path } else {
    Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
if (-not (Test-Path (Join-Path $root "START_APP.bat"))) {
    Write-Host "[错误] 不是 ONYX 项目目录: $root" -ForegroundColor Red
    exit 1
}

function Get-Python {
    if ($env:AI_AGENT_PYTHON -and (Test-Path $env:AI_AGENT_PYTHON)) { return $env:AI_AGENT_PYTHON }
    foreach ($p in @(
        "$env:USERPROFILE\miniconda3\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
    )) { if (Test-Path $p) { return $p } }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return "python"
}

function Invoke-NpmInstall($prefix) {
    $npm = Join-Path $root "scripts\npm.cjs"
    if ($prefix) { & node $npm install --prefix (Join-Path $root $prefix) }
    else { & node $npm install }
    if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
}

Write-Host "ONYX-OVERRIDE 安装 — $root" -ForegroundColor Cyan
$py = Get-Python

if (-not (Test-Path (Join-Path $root "node_modules"))) { Invoke-NpmInstall $null }
if (-not (Test-Path (Join-Path $root "frontend\node_modules"))) { Invoke-NpmInstall "frontend" }

$req = Join-Path $root "backend\requirements.txt"
if (Test-Path $req) { & $py -m pip install -r $req -q }
if (-not $SkipPlaywright) {
    $extras = Join-Path $root "backend\requirements-extras.txt"
    if (Test-Path $extras) {
        & $py -m pip install -r $extras -q
        $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:LOCALAPPDATA "ms-playwright"
        & $py -m playwright install chromium 2>$null
    }
}

$envFile = Join-Path $root "backend\.env"
$envExample = Join-Path $root "backend\.env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) { Copy-Item -Force $envExample $envFile }

if (-not $SkipBuild -and -not (Test-Path (Join-Path $root "frontend\build\index.html"))) {
    & node (Join-Path $root "scripts\npm.cjs") run build --prefix (Join-Path $root "frontend")
}

if (-not $NoShortcut) {
    $sc = Join-Path $root "scripts\create-desktop-shortcut.ps1"
    if (Test-Path $sc) { & powershell -NoProfile -ExecutionPolicy Bypass -File $sc }
}

Write-Host "完成。启动: START_APP.bat 或桌面 ONYX-OVERRIDE 快捷方式" -ForegroundColor Green
