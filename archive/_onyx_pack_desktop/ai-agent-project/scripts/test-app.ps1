# 启动前自检：品牌资源、前端构建、后端健康、Electron 能否拉起
param([switch]$SkipElectron)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$py = "$env:USERPROFILE\miniconda3\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "`n=== ONYX-OVERRIDE 应用自检 ===" -ForegroundColor Cyan

# 1) 品牌与图标
& $py (Join-Path $root "scripts\build-branding.py")
$required = @(
    "assets\branding\onyx-override-hero.png",
    "electron\icon-1024.png",
    "electron\icon.ico",
    "frontend\public\logo-256.png"
)
foreach ($f in $required) {
    if (-not (Test-Path (Join-Path $root $f))) { throw "缺少文件: $f" }
    Write-Host "  OK  $f" -ForegroundColor DarkGray
}

# 2) 前端生产包
$buildIndex = Join-Path $root "frontend\build\index.html"
if (-not (Test-Path $buildIndex)) {
    Write-Host "构建前端…" -ForegroundColor Yellow
    node (Join-Path $root "scripts\npm.cjs") run build --prefix (Join-Path $root "frontend")
}
if (-not (Test-Path $buildIndex)) { throw "frontend/build 不存在" }
Write-Host "  OK  frontend/build" -ForegroundColor DarkGray

# 3) 后端健康（若未运行则临时启动）
$healthOk = $false
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
    $healthOk = ($r.StatusCode -eq 200)
} catch { }

$backendProc = $null
if (-not $healthOk) {
    Write-Host "临时启动后端…" -ForegroundColor Yellow
    $backendProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$root\scripts\start-backend.cmd`"" -WindowStyle Hidden -PassThru
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { $healthOk = $true; break }
        } catch { }
    }
}
if (-not $healthOk) { throw "后端 /health 无响应" }
Write-Host "  OK  GET /health" -ForegroundColor DarkGray

try {
    $doc = Invoke-RestMethod -Uri "http://127.0.0.1:8000/meta/doctor" -TimeoutSec 5
    Write-Host "  OK  /meta/doctor status=$($doc.status)" -ForegroundColor DarkGray
} catch {
    Write-Host "  WARN /meta/doctor: $_" -ForegroundColor Yellow
}

# 4) Electron 冒烟（可选）
if (-not $SkipElectron) {
    Write-Host "启动 Electron 5 秒冒烟…" -ForegroundColor Yellow
    $env:NODE_ENV = "production"
    $electron = Start-Process -FilePath "node" -ArgumentList @(
        (Join-Path $root "scripts\npm.cjs"), "run", "electron"
    ) -WorkingDirectory $root -PassThru -WindowStyle Normal
    Start-Sleep -Seconds 5
    if ($electron.HasExited) { throw "Electron 过早退出 (code $($electron.ExitCode))" }
    Stop-Process -Id $electron.Id -Force -ErrorAction SilentlyContinue
    Get-Process -Name "electron" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  OK  Electron 已启动并正常退出测试" -ForegroundColor DarkGray
}

if ($backendProc) {
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
}

Write-Host "`n全部自检通过。可双击桌面「ONYX-OVERRIDE」或运行 START_APP.bat`n" -ForegroundColor Green
