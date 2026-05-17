# 重新生成高清 ICO 并刷新桌面快捷方式图标
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$py = "$env:USERPROFILE\miniconda3\python.exe"
& $py (Join-Path $root "scripts\build-branding.py")
node (Join-Path $root "scripts\npm.cjs") run build --prefix (Join-Path $root "frontend")
& (Join-Path $root "scripts\create-desktop-shortcut.ps1")
Write-Host ""
Write-Host "若桌面仍糊：按 F5 刷新；仍不行请注销/重启，或删除旧快捷方式后只用新生成的 .lnk" -ForegroundColor Yellow
