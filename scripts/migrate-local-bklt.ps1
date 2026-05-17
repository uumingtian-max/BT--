param(
  [switch]$RemoveLegacy,
  [switch]$NoGitPull
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Desktop = [Environment]::GetFolderPath("Desktop")
$NewLauncher = Join-Path $Root "Launch-BKLT-Blacklight.vbs"
$OldLauncher = Join-Path $Root "Launch-ONYX-OVERRIDE.vbs"
$StartApp = Join-Path $Root "START_APP.bat"
$Shortcut = Join-Path $Desktop "BKLT 黑光.lnk"
$BackupDir = Join-Path $Root ".bklt-migration-backup"
$LogDir = Join-Path $Root "logs"
$LogFile = Join-Path $LogDir "bklt-migration.log"

function Write-Step([string]$Message) {
  $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
  Write-Host $line
  Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

Ensure-Dir $LogDir
Write-Step "BKLT local migration started. Root=$Root"

if (-not (Test-Path -LiteralPath $Root)) {
  throw "Project root not found: $Root"
}

Set-Location $Root

if (-not $NoGitPull -and (Test-Path -LiteralPath (Join-Path $Root ".git"))) {
  $git = Get-Command git -ErrorAction SilentlyContinue
  if ($git) {
    Write-Step "Running git pull --ff-only..."
    try {
      git pull --ff-only | Tee-Object -FilePath $LogFile -Append
    } catch {
      Write-Step "WARN: git pull failed. Keeping local files untouched. Reason: $($_.Exception.Message)"
    }
  } else {
    Write-Step "WARN: git not found in PATH; skipping git pull."
  }
}

$launcherContent = @'
' BKLT 黑光桌面快捷方式启动器 — 隐藏窗口运行，便于绑定高清 .ico（避免 .bat 图标被系统忽略）
Set sh = CreateObject("WScript.Shell")
root = Replace(WScript.ScriptFullName, "Launch-BKLT-Blacklight.vbs", "")
sh.CurrentDirectory = root
sh.Run "cmd /c """ & root & "START_APP.bat""", 0, False
'@

Set-Content -LiteralPath $NewLauncher -Value $launcherContent -Encoding ASCII
Write-Step "Ensured BKLT launcher: $NewLauncher"

if (Test-Path -LiteralPath $StartApp) {
  $bat = Get-Content -LiteralPath $StartApp -Raw -Encoding UTF8
  $bat = $bat -replace 'title ONYX-OVERRIDE', 'title BKLT 黑光'
  $bat = $bat -replace '\[ONYX\]', '[BKLT]'
  Set-Content -LiteralPath $StartApp -Value $bat -Encoding UTF8
  Write-Step "Updated START_APP.bat branding."
} else {
  Write-Step "WARN: START_APP.bat not found: $StartApp"
}

$wscript = Join-Path $env:WINDIR "System32\wscript.exe"
if (-not (Test-Path -LiteralPath $wscript)) {
  throw "wscript.exe not found: $wscript"
}

$iconCandidates = @(
  (Join-Path $Root "electron\icon.ico"),
  (Join-Path $Root "assets\branding\icon.ico"),
  (Join-Path $Root "assets\branding\bklt.ico")
)
$icon = $iconCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

$sh = New-Object -ComObject WScript.Shell
$link = $sh.CreateShortcut($Shortcut)
$link.TargetPath = $wscript
$link.Arguments = "`"$NewLauncher`""
$link.WorkingDirectory = $Root
$link.Description = "BKLT 黑光 / BLACKLIGHT local AI Agent workbench"
if ($icon) { $link.IconLocation = $icon }
$link.Save()
Write-Step "Created/updated desktop shortcut: $Shortcut"

$oldShortcutNames = @(
  "ONYX-OVERRIDE.lnk",
  "ONYX OVERRIDE.lnk",
  "Onyx Override.lnk",
  "BLACKLIGHT.lnk"
)
foreach ($name in $oldShortcutNames) {
  $p = Join-Path $Desktop $name
  if (Test-Path -LiteralPath $p) {
    if ($RemoveLegacy) {
      Remove-Item -LiteralPath $p -Force
      Write-Step "Removed legacy shortcut: $p"
    } else {
      Ensure-Dir $BackupDir
      Move-Item -LiteralPath $p -Destination (Join-Path $BackupDir $name) -Force
      Write-Step "Moved legacy shortcut to backup: $p"
    }
  }
}

if (Test-Path -LiteralPath $OldLauncher) {
  if ($RemoveLegacy) {
    Remove-Item -LiteralPath $OldLauncher -Force
    Write-Step "Removed legacy launcher: $OldLauncher"
  } else {
    Ensure-Dir $BackupDir
    Move-Item -LiteralPath $OldLauncher -Destination (Join-Path $BackupDir "Launch-ONYX-OVERRIDE.vbs") -Force
    Write-Step "Moved legacy launcher to backup: $OldLauncher"
  }
}

Write-Step "BKLT migration completed. Desktop shortcut target is now: $wscript $NewLauncher"
Write-Host ""
Write-Host "完成：桌面 BKLT 黑光快捷方式已更新。" -ForegroundColor Green
Write-Host "日志：$LogFile" -ForegroundColor Cyan
