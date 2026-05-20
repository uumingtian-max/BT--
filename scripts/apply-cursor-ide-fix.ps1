# 一键修复 Cursor 问题面板（conda terminal.py / basedpyright 误报）
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$cursorSettings = Join-Path $env:APPDATA "Cursor\User\settings.json"
$ws = Join-Path $root "ai-agent-project.code-workspace"

Write-Host "`n=== Cursor IDE 一键修复 ===" -ForegroundColor Cyan

# 1) 卸载 Edge DevTools（CSS 误报）
if (Get-Command cursor -ErrorAction SilentlyContinue) {
  Write-Host "卸载 Edge DevTools 扩展..." -ForegroundColor DarkGray
  try { cursor --uninstall-extension ms-edgedevtools.vscode-edge-devtools 2>&1 | Out-Null } catch {}
}

# 2) 合并用户级 settings（cursorpyright 全局关闭类型检查 + conda 当纯文本）
$patch = @{
  python = @{
    defaultInterpreterPath = "C:\Users\ROG\miniconda3\envs\bt-heiguang\python.exe"
    analysis = @{
      typeCheckingMode = "off"
      diagnosticMode   = "openFilesOnly"
      exclude          = @("**/miniconda3/**", "**/site-packages/**", "**/_pytest/**")
      ignore           = @("**/miniconda3/**", "**/site-packages/**")
    }
  }
  cursorpyright = @{
    analysis = @{
      typeCheckingMode              = "off"
      diagnosticMode                = "openFilesOnly"
      useLibraryCodeForTypes        = $false
      exclude                       = @(
        "C:/Users/ROG/miniconda3/**",
        "C:/Users/ROG/Desktop/miniconda3/**",
        "**/miniconda3/**",
        "**/site-packages/**",
        "**/_pytest/**"
      )
      ignore                        = @(
        "C:/Users/ROG/miniconda3/**",
        "C:/Users/ROG/Desktop/miniconda3/**",
        "**/miniconda3/**",
        "**/site-packages/**"
      )
      diagnosticSeverityOverrides = @{
        reportMissingImports         = "none"
        reportMissingModuleSource    = "none"
        reportGeneralTypeIssues      = "none"
      }
    }
  }
  "css.validate" = $false
  "files.associations" = @{
    "**/miniconda3/**"     = "plaintext"
    "**/site-packages/**" = "plaintext"
    "**/_pytest/**"       = "plaintext"
  }
}

function Merge-Hashtable($base, $over) {
  foreach ($k in $over.Keys) {
    if ($base.ContainsKey($k) -and $base[$k] -is [hashtable] -and $over[$k] -is [hashtable]) {
      Merge-Hashtable $base[$k] $over[$k]
    } else {
      $base[$k] = $over[$k]
    }
  }
}

$current = @{}
if (Test-Path $cursorSettings) {
  try {
    $raw = Get-Content $cursorSettings -Raw -Encoding UTF8
    $current = $raw | ConvertFrom-Json -AsHashtable
  } catch {
    Write-Host "警告: 无法解析现有 settings，将写入关键项" -ForegroundColor Yellow
    $current = @{}
  }
}
Merge-Hashtable $current $patch
($current | ConvertTo-Json -Depth 20) | Set-Content $cursorSettings -Encoding UTF8
Write-Host "已更新: $cursorSettings" -ForegroundColor Green

# 3) 用工作区打开项目
if (Test-Path $ws) {
  Write-Host "打开工作区: $ws" -ForegroundColor Green
  if (Get-Command cursor -ErrorAction SilentlyContinue) {
    Start-Process cursor -ArgumentList @($ws)
  }
}

# 4) 验证 CLI pyright
$py = "$env:USERPROFILE\miniconda3\envs\bt-heiguang\python.exe"
if (Test-Path $py) {
  Push-Location $root
  $out = & $py -m pyright backend scripts start.py 2>&1 | Select-Object -Last 1
  Pop-Location
  Write-Host "pyright: $out" -ForegroundColor $(if ($out -match "0 errors") { "Green" } else { "Yellow" })
}

Write-Host "`n请在 Cursor 中: Ctrl+Shift+P -> Cursor Pyright: Restart Server -> Reload Window`n" -ForegroundColor Cyan
