#!/usr/bin/env bash
set -u

PROJECT_DIR="/mnt/c/Users/ROG/Desktop/ai-agent-project"
LOG="$PROJECT_DIR/vllm-gemma.log"
PID_FILE="$PROJECT_DIR/vllm-gemma.pid"

if [[ -f "$PID_FILE" ]]; then
  PID="$(cat "$PID_FILE")"
  echo "PID=$PID"
  ps -p "$PID" -o pid,stat,cmd || true
fi

pgrep -af "vllm.entrypoints.openai.api_server" || true
pgrep -af "EngineCore" || true

if [[ -f "$LOG" ]]; then
  echo "LOG=$LOG"
  tail -n 120 "$LOG"
else
  echo "missing log: $LOG"
fi
