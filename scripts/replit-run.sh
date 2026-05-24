#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[BKLT/Replit] Installing Python dependencies..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

echo "[BKLT/Replit] Installing frontend dependencies..."
npm install
npm install --prefix frontend

echo "[BKLT/Replit] Building frontend for /mobile preview..."
npm run build --prefix frontend

export BACKEND_HOST="0.0.0.0"
export BACKEND_PORT="8000"
export HABIT_CHECK_ENABLED="false"
export OLLAMA_WARM_ON_STARTUP="0"
export AGENT_TOOL_AUTO_CONFIRM="0"
export REQUIRE_API_TOKEN_ON_LAN="0"
export LLM_BACKEND="ollama"
export OLLAMA_HOST="http://127.0.0.1:11434"
export AGENT_DEFAULT_MODEL="qwen3.5:9b"
export CORS_ORIGINS="*"
export UVICORN_RELOAD="0"
export UVICORN_HOST="0.0.0.0"

cat > backend/.env <<'ENV'
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
HABIT_CHECK_ENABLED=false
OLLAMA_WARM_ON_STARTUP=0
AGENT_TOOL_AUTO_CONFIRM=0
REQUIRE_API_TOKEN_ON_LAN=0
LLM_BACKEND=ollama
OLLAMA_HOST=http://127.0.0.1:11434
AGENT_DEFAULT_MODEL=qwen3.5:9b
CORS_ORIGINS=*
ENV

echo "[BKLT/Replit] Starting FastAPI preview on 0.0.0.0:8000"
echo "[BKLT/Replit] Open /health for backend status, /mobile for the built frontend preview."
cd backend
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
