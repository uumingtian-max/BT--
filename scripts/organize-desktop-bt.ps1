# BT desktop layout per docs/项目整理指南.md
$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Projects = Join-Path $Desktop "Projects"
$Shortcuts = Join-Path $Desktop "Shortcuts"
$Tools = Join-Path $Desktop "Tools"
$Workspace = Join-Path $Desktop "Workspace"
$Archive = Join-Path $Projects "Archive"

foreach ($d in @($Projects, "$Projects\BT-Backups", $Archive, $Shortcuts, $Tools, $Workspace)) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

$src = Join-Path $Desktop "ai-agent-project"
$dst = Join-Path $Projects "BT-Blacklight"
if ((Test-Path $src) -and -not (Test-Path $dst)) {
    Move-Item -LiteralPath $src -Destination $dst
}

$backup = Join-Path $Desktop "ai-agent-project-upgraded-review"
$backupDst = Join-Path $Projects "BT-Backups\ai-agent-project-upgraded-review"
if ((Test-Path $backup) -and -not (Test-Path $backupDst)) {
    Move-Item -LiteralPath $backup -Destination $backupDst
}

foreach ($name in @("AI 工具", "创作与浏览", "开发协作")) {
    $from = Join-Path $Desktop $name
    $to = Join-Path $Workspace $name
    if ((Test-Path $from) -and -not (Test-Path $to)) {
        Move-Item -LiteralPath $from -Destination $to
    }
}

$mergecheck = Join-Path $Desktop "_bt_mergecheck"
if (Test-Path $mergecheck) {
    Remove-Item -LiteralPath $mergecheck -Recurse -Force -ErrorAction SilentlyContinue
}

$firefox = Join-Path $Desktop "Firefox.exe"
if (Test-Path $firefox) {
    Remove-Item -LiteralPath $firefox -Force
}

foreach ($item in @("torch-2.5.1+cu124-cp311-cp311-win_amd64.whl", "Run-HKLM-backup.reg")) {
    $from = Join-Path $Desktop $item
    if (Test-Path $from) {
        Move-Item -LiteralPath $from -Destination (Join-Path $Tools $item) -Force
    }
}

$png = Join-Path $Desktop "0b8da31c-d114-40c9-a0cd-0733125b3a92.png"
if (Test-Path $png) {
    Move-Item -LiteralPath $png -Destination (Join-Path $Archive "0b8da31c-d114-40c9-a0cd-0733125b3a92.png") -Force
}

$guide = Join-Path $Desktop "项目整理指南.md"
$btDocs = Join-Path $Projects "BT-Blacklight\docs\项目整理指南.md"
if ((Test-Path $guide) -and (Test-Path (Split-Path $btDocs -Parent))) {
    Copy-Item -LiteralPath $guide -Destination $btDocs -Force
    Remove-Item -LiteralPath $guide -Force
}

$lnkNames = @(
    "BT（黑光）.lnk", "打开 BT（黑光）.lnk", "Continue.lnk",
    "Docker Desktop.lnk", "GitHub Desktop.lnk", "GitHub.lnk",
    "NVIDIA Sync.lnk", "Reddit.lnk"
)
foreach ($n in $lnkNames) {
    $from = Join-Path $Desktop $n
    if (Test-Path $from) {
        $to = Join-Path $Shortcuts $n
        if (-not (Test-Path $to)) { Move-Item -LiteralPath $from -Destination $to }
        else { Remove-Item -LiteralPath $from -Force }
    }
}

$btRoot = Join-Path $Projects "BT-Blacklight"
$icon = Join-Path $btRoot "electron\icon.ico"
$startLnk = Join-Path $Shortcuts "Start-BT-Blacklight.lnk"
if ((Test-Path $btRoot) -and -not (Test-Path $startLnk)) {
    $WshShell = New-Object -ComObject WScript.Shell
    $sc = $WshShell.CreateShortcut($startLnk)
    $sc.TargetPath = "C:\Windows\System32\cmd.exe"
    $sc.Arguments = "/c `"cd /d `"$btRoot`" && python start.py app`""
    $sc.WorkingDirectory = $btRoot
    if (Test-Path $icon) { $sc.IconLocation = "$icon,0" }
    $sc.Description = "Start BT (Blacklight)"
    $sc.Save()
}

$wsOld = Join-Path $btRoot "ai-agent-project.code-workspace"
$wsNew = Join-Path $btRoot "BT-Blacklight.code-workspace"
if (Test-Path $wsOld) {
    $json = Get-Content -Raw -Encoding UTF8 $wsOld | ConvertFrom-Json
    $json.folders[0].name = "BT-Blacklight"
    $json.folders[0].path = $btRoot.Replace("\", "\\")
    $json | ConvertTo-Json -Depth 10 | Set-Content -Path $wsNew -Encoding UTF8
    if ($wsOld -ne $wsNew) { Remove-Item $wsOld -Force }
}

Write-Host "Desktop organize done. BT root: $btRoot"
