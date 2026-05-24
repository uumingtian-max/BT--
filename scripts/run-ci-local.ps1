# 本地复现 CI（须在仓库根目录执行）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$env:LLM_BACKEND = "ollama"
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:AGENT_DEFAULT_MODEL = "qwen3.5:9b"
$env:HABIT_CHECK_ENABLED = "false"

Write-Host "== backend: pytest ==" -ForegroundColor Cyan
python -m pytest backend/tests/ -q

Write-Host "== backend: ruff ==" -ForegroundColor Cyan
ruff check backend/
ruff format --check backend/

Write-Host "== backend: py_compile ==" -ForegroundColor Cyan
python -m py_compile start.py backend/main.py backend/automation_runner.py backend/run_graph_store.py

Write-Host "== frontend: build + test ==" -ForegroundColor Cyan
Push-Location frontend
npm ci
npm run lint --if-present
npm run build
npm test
Pop-Location

Write-Host "OK: local CI checks passed." -ForegroundColor Green
Write-Host "Note: GitHub Actions may still show red X if the account billing is locked." -ForegroundColor Yellow
