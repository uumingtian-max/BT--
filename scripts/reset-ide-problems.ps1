# 关闭 conda/pytest 误报：请用本脚本后重载 Cursor/VS Code
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n=== 重置 IDE 问题面板 ===" -ForegroundColor Cyan
Write-Host "A. 扩展 -> 搜索 Based Pyright -> 卸载（或禁用）"
Write-Host "   截图里的 basedpyright(reportMissingImports) 来自该扩展，与项目代码无关"
Write-Host "B. 问题面板 -> 右键 terminal.py -> 关闭 / 从问题中移除"
Write-Host "C. 文件 -> 打开工作区 -> ai-agent-project.code-workspace"
Write-Host "D. Ctrl+Shift+P -> BasedPyright: Restart Server（若未卸载）"
Write-Host "E. Ctrl+Shift+P -> Developer: Reload Window`n"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ws = Join-Path $root "ai-agent-project.code-workspace"
if (Test-Path $ws) {
  Write-Host "工作区: $ws" -ForegroundColor Green
}

Write-Host "验证 pyright（应 0 error）..." -ForegroundColor DarkGray
$candidates = @(
  "$env:USERPROFILE\Desktop\miniconda3\envs\bt-heiguang\python.exe",
  "$env:USERPROFILE\miniconda3\envs\bt-heiguang\python.exe"
)
$py = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($py) {
  Push-Location $root
  & $py -m pyright backend scripts start.py 2>&1 | Select-Object -Last 3
  Pop-Location
}

Write-Host "`n若仍见 terminal.py：一定是 Based Pyright 未卸载或未 Reload。`n" -ForegroundColor Yellow
