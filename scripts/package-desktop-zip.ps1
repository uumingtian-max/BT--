# 打包 ONYX-OVERRIDE 到桌面 ZIP（不含 node_modules，体积可控）
$ErrorActionPreference = "Stop"
param(
    [switch]$ConfirmPackage
)

if (-not $ConfirmPackage) {
    Write-Host "BLOCKED: this script builds and writes ZIP artifacts to Desktop/C:." -ForegroundColor Red
    Write-Host "Run only after explicit user approval: .\scripts\package-desktop-zip.ps1 -ConfirmPackage" -ForegroundColor Yellow
    exit 2
}
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$desktop = [Environment]::GetFolderPath("Desktop")
$version = "1.1.0"
$zipName = "ONYX-OVERRIDE-v$version.zip"
$zipPath = Join-Path $desktop $zipName
$staging = Join-Path $env:TEMP "onyx-override-pack-$(Get-Date -Format 'yyyyMMddHHmmss')"
$dest = Join-Path $staging "ONYX-OVERRIDE"

Write-Host "ONYX-OVERRIDE 打包" -ForegroundColor Cyan
Write-Host "  源: $root"

# 构建前端
if (Test-Path (Join-Path $root "frontend\package.json")) {
    Write-Host "  构建前端…" -ForegroundColor Gray
    node (Join-Path $root "scripts\npm.cjs") run build --prefix (Join-Path $root "frontend")
}

# 品牌图标
$py = "$env:USERPROFILE\miniconda3\python.exe"
if (Test-Path $py) {
    & $py (Join-Path $root "scripts\build-branding.py") | Out-Null
}

$excludeDir = @(
    "node_modules", "frontend\node_modules", "__pycache__", ".pytest_cache",
    ".git", ".cursor", "agent-transcripts", "terminals", "logs"
)
$excludeFile = @("*.pyc", "*.pyo", ".DS_Store", "Thumbs.db", "*.log", "*.pid")

function Should-Skip($rel) {
    $r = $rel -replace '/', '\'
    foreach ($d in $excludeDir) {
        if ($r -eq $d -or $r.StartsWith("$d\")) { return $true }
    }
    # 隐私：本机 .env 与备份；保留 *.example 模板
    if ($r -eq '.env') { return $true }
    if ($r -eq 'backend\.env') { return $true }
    if ($r.StartsWith('backend\.env.') -and $r -notmatch '\.example$') { return $true }
    return $false
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null
$files = Get-ChildItem -Path $root -Recurse -File -Force
$count = 0
foreach ($f in $files) {
    $rel = $f.FullName.Substring($root.Length).TrimStart('\')
    if (Should-Skip $rel) { continue }
    $skip = $false
    foreach ($pat in $excludeFile) {
        if ($f.Name -like $pat) { $skip = $true; break }
    }
    if ($skip) { continue }
    $out = Join-Path $dest $rel
    $dir = Split-Path $out -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Copy-Item -Force $f.FullName $out
    $count++
}

@'
ONYX-OVERRIDE 便携包
==================

1. 解压到任意目录（路径尽量无中文空格问题）
2. 双击 INSTALL_FIRST_RUN.bat（仅首次，安装 Node 依赖）
3. 复制 backend\.env.example 为 backend\.env，按你的环境填写（本 ZIP 不含 .env，避免泄露密钥与路径）
4. 安装 Ollama: https://ollama.com ，执行 scripts\MANAGE_MODELS.ps1 拉取五模型栈（或改用 vLLM 见 README）
5. 双击 START_APP.bat 启动

可选：运行 scripts\create-desktop-shortcut.ps1 创建带品牌图标的桌面快捷方式。

详见 README.md
'@ | Set-Content -Path (Join-Path $dest "请先阅读-安装说明.txt") -Encoding UTF8

if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Compress-Archive -Path $dest -DestinationPath $zipPath -CompressionLevel Optimal
Remove-Item -Recurse -Force $staging

$mb = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-Host ""
Write-Host "完成: $zipPath" -ForegroundColor Green
Write-Host "  文件数: $count  大小: ${mb} MB" -ForegroundColor Green

# 第二份：C 盘根目录（无权限则落到用户主目录）
$cRootZip = Join-Path "C:\" $zipName
$cFallback = Join-Path $env:USERPROFILE $zipName
try {
    Copy-Item -LiteralPath $zipPath -Destination $cRootZip -Force
    Write-Host "完成: $cRootZip" -ForegroundColor Green
    Write-Host "  大小: ${mb} MB（与桌面份相同）" -ForegroundColor Green
} catch {
    Write-Host "C:\ 写入失败（可能需管理员权限），改写到: $cFallback" -ForegroundColor Yellow
    Copy-Item -LiteralPath $zipPath -Destination $cFallback -Force
    Write-Host "完成: $cFallback" -ForegroundColor Green
}
