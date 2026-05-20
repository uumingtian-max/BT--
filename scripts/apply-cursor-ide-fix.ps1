# 一键修复 Cursor 问题面板（cursorpyright 扫 conda / terminal.py 误报）
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$cursorSettings = Join-Path $env:APPDATA "Cursor\User\settings.json"
$ws = Join-Path $root "ai-agent-project.code-workspace"

Write-Host "`n=== Cursor IDE 一键修复 ===" -ForegroundColor Cyan

if (Get-Command cursor -ErrorAction SilentlyContinue) {
  Write-Host "卸载 Edge DevTools（若已装）..." -ForegroundColor DarkGray
  try { cursor --uninstall-extension ms-edgedevtools.vscode-edge-devtools 2>&1 | Out-Null } catch {}
}

# VS Code/Cursor 只认扁平键名 python.* / cursorpyright.*，不能写嵌套 JSON
$flat = [ordered]@{
  "python.defaultInterpreterPath" = "C:\Users\ROG\miniconda3\envs\bt-heiguang\python.exe"
  "python.analysis.typeCheckingMode" = "off"
  "python.analysis.diagnosticMode" = "openFilesOnly"
  "python.analysis.exclude" = @("**/miniconda3/**", "**/site-packages/**", "**/_pytest/**")
  "python.analysis.ignore" = @("**/miniconda3/**", "**/site-packages/**")
  "cursorpyright.analysis.typeCheckingMode" = "off"
  "cursorpyright.analysis.diagnosticMode" = "openFilesOnly"
  "cursorpyright.analysis.useLibraryCodeForTypes" = $false
  "cursorpyright.analysis.exclude" = @(
    "C:/Users/ROG/miniconda3/**", "C:/Users/ROG/Desktop/miniconda3/**",
    "**/miniconda3/**", "**/site-packages/**", "**/_pytest/**"
  )
  "cursorpyright.analysis.ignore" = @(
    "C:/Users/ROG/miniconda3/**", "C:/Users/ROG/Desktop/miniconda3/**",
    "**/miniconda3/**", "**/site-packages/**"
  )
  "cursorpyright.analysis.diagnosticSeverityOverrides" = @{
    reportMissingImports = "none"
    reportMissingModuleSource = "none"
    reportGeneralTypeIssues = "none"
  }
  "css.validate" = $false
  "files.associations" = @{
    "**/miniconda3/**" = "plaintext"
    "**/site-packages/**" = "plaintext"
    "**/_pytest/**" = "plaintext"
  }
}

$current = [ordered]@{}
if (Test-Path $cursorSettings) {
  try {
    $obj = Get-Content $cursorSettings -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($p in $obj.PSObject.Properties) { $current[$p.Name] = $p.Value }
  } catch {
    Write-Host "警告: 无法解析现有 settings，仅写入 IDE 修复项" -ForegroundColor Yellow
  }
}
foreach ($k in $flat.Keys) { $current[$k] = $flat[$k] }
($current | ConvertTo-Json -Depth 20) | Set-Content $cursorSettings -Encoding UTF8
Write-Host "已更新: $cursorSettings" -ForegroundColor Green

if (Test-Path $ws) {
  Write-Host "打开工作区: $ws" -ForegroundColor Green
  if (Get-Command cursor -ErrorAction SilentlyContinue) {
    Start-Process cursor -ArgumentList @($ws)
  }
}

$py = "$env:USERPROFILE\miniconda3\envs\bt-heiguang\python.exe"
if (Test-Path $py) {
  Push-Location $root
  $out = & $py -m pyright backend scripts start.py 2>&1 | Select-Object -Last 1
  Pop-Location
  Write-Host "pyright: $out" -ForegroundColor Green
}

Write-Host "`n在 Cursor: Ctrl+Shift+P -> Cursor Pyright: Restart Server -> Reload Window`n" -ForegroundColor Cyan
