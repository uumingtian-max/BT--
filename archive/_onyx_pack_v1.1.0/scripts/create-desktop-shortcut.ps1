# 桌面快捷方式 — ONYX-OVERRIDE（高清图标，经 VBS 启动避免 .bat 图标失效）
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$launcher = Join-Path $root "Launch-ONYX-OVERRIDE.vbs"
$py = "$env:USERPROFILE\miniconda3\python.exe"
$icon = Join-Path $root "electron\icon.ico"
$brandIco = Join-Path $root "assets\branding\desktop-icon.ico"
$desktop = [Environment]::GetFolderPath("Desktop")
if (-not (Test-Path $launcher)) { throw "找不到 $launcher" }

if (Test-Path $py) { & $py (Join-Path $root "scripts\build-branding.py") }
if (Test-Path $brandIco) { Copy-Item -Force $brandIco $icon }

function New-Shortcut($name) {
    $lnk = Join-Path $desktop "$name.lnk"
    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($lnk)
    $sc.TargetPath = "$env:SystemRoot\System32\wscript.exe"
    $sc.Arguments = "`"$launcher`""
    $sc.WorkingDirectory = $root
    $sc.WindowStyle = 1
    $sc.Description = "ONYX-OVERRIDE — 本地智能助手"
    if (Test-Path $icon) { $sc.IconLocation = "$icon,0" }
    $sc.Save()
    Write-Host "  $lnk" -ForegroundColor Green
}

Write-Host "ONYX-OVERRIDE 桌面快捷方式" -ForegroundColor Cyan
New-Shortcut "ONYX-OVERRIDE"
New-Shortcut "打开 ONYX-OVERRIDE"
if (Test-Path $icon) { Write-Host "图标: $icon" }
