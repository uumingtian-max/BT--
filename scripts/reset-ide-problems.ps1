# 关闭 conda/pytest 误报：请用本脚本后重载 Cursor/VS Code
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n=== 重置 IDE 问题面板 ===" -ForegroundColor Cyan
Write-Host "1. 关闭所有 miniconda3 / site-packages / _pytest 相关标签页"
Write-Host "2. 用工作区打开: ai-agent-project.code-workspace"
Write-Host "3. Ctrl+Shift+P -> Developer: Reload Window"
Write-Host "4. 扩展里禁用: Microsoft Edge Tools for VS Code`n"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ws = Join-Path $root "ai-agent-project.code-workspace"
if (Test-Path $ws) {
  Write-Host "工作区文件: $ws" -ForegroundColor Green
}

Write-Host "验证项目内 pyright ..." -ForegroundColor DarkGray
$py = "$env:USERPROFILE\miniconda3\envs\bt-heiguang\python.exe"
if (Test-Path $py) {
  Push-Location $root
  & $py -m pyright backend 2>&1 | Select-Object -Last 1
  Pop-Location
}

Write-Host "`n完成。App.css 不应再有告警；terminal.py 不应再打开。`n" -ForegroundColor Green
