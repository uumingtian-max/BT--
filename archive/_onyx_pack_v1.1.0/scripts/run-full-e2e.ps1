# 全流程：补丁 -> 锤炼 x2 -> 全工具实机（可跳过超重 LLM 项）
param(
    [switch]$Quick,
    [switch]$SkipElectron
)

$ErrorActionPreference = "Stop"
$root = "c:\Users\ROG\Desktop\ai-agent-project"
$py = "$env:USERPROFILE\miniconda3\python.exe"

powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\ensure-patches.ps1")

$hammerArgs = @("-File", (Join-Path $root "scripts\hammer-test.ps1"), "-Rounds", "2")
if ($SkipElectron) { $hammerArgs += "-SkipElectron" }
powershell -ExecutionPolicy Bypass @hammerArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$env:PLAYWRIGHT_BROWSERS_PATH = "$env:LOCALAPPDATA\ms-playwright"
$env:ENABLE_IMAGE_PLACEHOLDER = "1"
if ($Quick) { $env:TOOL_LIVE_QUICK = "1" }

$env:SKIP_ENSURE_PATCHES = "1"
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\run-tools-live.ps1")
exit $LASTEXITCODE
