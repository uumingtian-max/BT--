# 本地复现 CI（须在仓库根目录执行）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$env:LLM_BACKEND = "ollama"
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:AGENT_DEFAULT_MODEL = "qwen3.5:9b"
$env:HABIT_CHECK_ENABLED = "false"
python -m pytest backend/tests/ -q
ruff check backend/
ruff format --check backend/
Push-Location frontend
npm run build
Pop-Location
Write-Host "OK: local CI checks passed." -ForegroundColor Green
