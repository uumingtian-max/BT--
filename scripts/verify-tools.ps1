# 工具接入自检：核查 -> 执行(pytest) -> 验证(可选联网) -> 提示运行
# 用法: powershell -ExecutionPolicy Bypass -File scripts\verify-tools.ps1
#       加 -LiveNetwork 会跑真实 web_search（需 ddgs + 网络）

param([switch]$LiveNetwork)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backend = Join-Path $root "backend"

Write-Host ""
Write-Host "=== [1/4] 核查：tools 文件与 agent 注册 ===" -ForegroundColor Cyan

$toolFiles = @(
  "__init__.py", "search.py", "local_crawl.py", "file_ops.py",
  "code_exec.py", "external_control.py"
)
foreach ($f in $toolFiles) {
  $p = Join-Path $backend "tools\$f"
  if (-not (Test-Path $p)) { throw "缺少 $p" }
  Write-Host "  OK  tools\$f"
}

$py = $env:AI_AGENT_PYTHON
if (-not $py) {
  if (Test-Path "$env:USERPROFILE\miniconda3\python.exe") {
    $py = "$env:USERPROFILE\miniconda3\python.exe"
  } else {
    $py = "python"
  }
}

& $py -c @"
import sys
sys.path.insert(0, r'$backend')
from agent import TOOL_MAP
need = ['web_search','local_search','local_scrape_url','read_file','write_file','list_files','execute_python','open_url','open_path']
missing = [n for n in need if n not in TOOL_MAP]
if missing:
    raise SystemExit('TOOL_MAP 缺少: ' + ', '.join(missing))
print('  OK  TOOL_MAP 含', len(TOOL_MAP), '个工具')
"@

Write-Host ""
Write-Host "=== [2/4] 执行：pytest（含 test_tools_integration）===" -ForegroundColor Cyan
Push-Location $backend
try {
  & $py -m pytest tests -q --tb=short
  if ($LASTEXITCODE -ne 0) { throw "pytest 失败 exit=$LASTEXITCODE" }
} finally {
  Pop-Location
}

Write-Host ""
Write-Host "=== [3/4] 验证：可选联网搜索 ===" -ForegroundColor Cyan
if ($LiveNetwork) {
  $env:INTEGRATION_NETWORK = "1"
  Push-Location $backend
  try {
    & $py -m pytest tests/test_tools_integration.py::test_web_search_live_optional -v
  } finally {
    Pop-Location
    Remove-Item Env:INTEGRATION_NETWORK -ErrorAction SilentlyContinue
  }
} else {
  Write-Host "  跳过（加 -LiveNetwork 可测真实 web_search）"
}

Write-Host ""
Write-Host "=== [4/4] 运行提示 ===" -ForegroundColor Green
Write-Host "  后端: scripts\start-backend.cmd"
Write-Host "  桌面: ONYX-OVERRIDE.lnk"
Write-Host "  Agent 工具列表: GET http://127.0.0.1:8000/agent/tools"
Write-Host "  健康诊断:     GET http://127.0.0.1:8000/meta/doctor"
Write-Host "  定时任务:     GET http://127.0.0.1:8000/scheduler/jobs"
Write-Host "  消息网关:     GET http://127.0.0.1:8000/gateway/status"
Write-Host "  MCP 桥接:     GET http://127.0.0.1:8000/mcp/tools"
Write-Host "  会话搜索:     GET http://127.0.0.1:8000/chat/sessions/search?q=关键词"
Write-Host ""
Write-Host "全部核查通过。" -ForegroundColor Green
