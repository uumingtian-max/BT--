# 一键完成：依赖安装 -> 工具核查 -> 可选 Playwright -> 前端构建
# 用法: powershell -ExecutionPolicy Bypass -File scripts\setup-complete.ps1
#       加 -SkipPlaywright 跳过浏览器（体积大、耗时长）

param(
    [switch]$SkipPlaywright,
    [switch]$LiveNetwork
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backend = Join-Path $root "backend"

$py = $env:AI_AGENT_PYTHON
if (-not $py) {
    if (Test-Path "$env:USERPROFILE\miniconda3\python.exe") {
        $py = "$env:USERPROFILE\miniconda3\python.exe"
    } else {
        $py = "python"
    }
}

Write-Host ""
Write-Host "========== AI Agent 一键完成安装 ==========" -ForegroundColor Cyan
Write-Host "Python: $py"
Write-Host ""

Write-Host "[1/5] 安装 Python 依赖..." -ForegroundColor Yellow
& $py -m pip install -r (Join-Path $backend "requirements.txt") -q
if (-not $SkipPlaywright) {
    & $py -m pip install -r (Join-Path $backend "requirements-extras.txt") -q
}

Write-Host "[2/5] 安装前端依赖（若缺失）..." -ForegroundColor Yellow
if (-not (Test-Path (Join-Path $root "frontend\node_modules"))) {
    node (Join-Path $root "scripts\npm.cjs") install --prefix (Join-Path $root "frontend")
}
if (-not (Test-Path (Join-Path $root "node_modules"))) {
    node (Join-Path $root "scripts\npm.cjs") install
}

if (-not $SkipPlaywright) {
    Write-Host "[3/5] 安装 Playwright Chromium（浏览器工具）..." -ForegroundColor Yellow
    $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:LOCALAPPDATA "ms-playwright"
    & $py -m playwright install chromium
} else {
    Write-Host "[3/5] 跳过 Playwright（-SkipPlaywright）" -ForegroundColor DarkGray
}

Write-Host "[4/5] 后端测试 + 工具核查..." -ForegroundColor Yellow
Push-Location $backend
try {
    & $py -m pytest tests -q --tb=short
    if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
} finally {
    Pop-Location
}

$verifyArgs = @()
if ($LiveNetwork) { $verifyArgs += "-LiveNetwork" }
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\verify-tools.ps1") @verifyArgs

Write-Host "[5/5] 构建前端（Electron 生产包）..." -ForegroundColor Yellow
node (Join-Path $root "scripts\npm.cjs") run build --prefix (Join-Path $root "frontend")

Write-Host ""
Write-Host "========== 全部完成 ==========" -ForegroundColor Green
Write-Host "启动：双击桌面「ONYX-OVERRIDE」或「打开 ONYX-OVERRIDE」"
Write-Host "诊断：http://127.0.0.1:8000/meta/doctor"
Write-Host ""
