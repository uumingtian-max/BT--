#!/usr/bin/env bash
set -u

PROJECT_DIR="/mnt/c/Users/ROG/Desktop/ai-agent-project"
PID_FILE="$PROJECT_DIR/vllm-gemma.pid"

echo "=== nvidia-smi before ==="
nvidia-smi

MODEL_PID=""
if [[ -f "$PID_FILE" ]]; then
  MODEL_PID="$(cat "$PID_FILE")"
fi

echo "=== model pid ==="
echo "${MODEL_PID:-unknown}"

echo "=== vllm processes ==="
pgrep -af "vllm.entrypoints.openai.api_server" || true
pgrep -af "VLLM::EngineCore" || true

echo "=== candidate python processes ==="
pgrep -af "python" || true

echo "=== cleanup ==="
if [[ -n "$MODEL_PID" ]] && ps -p "$MODEL_PID" >/dev/null 2>&1; then
  for pid in $(pgrep -f "python|VLLM::EngineCore" || true); do
    if [[ "$pid" == "$MODEL_PID" ]]; then
      continue
    fi
    cmd="$(ps -p "$pid" -o cmd= 2>/dev/null || true)"
    if [[ "$cmd" == *"VLLM::EngineCore"* ]]; then
      echo "keep engine core: $pid $cmd"
      continue
    fi
    if [[ "$cmd" == *"vllm.entrypoints.openai.api_server"* ]]; then
      echo "keep vllm api: $pid $cmd"
      continue
    fi
    if [[ "$cmd" == *"python"* ]]; then
      echo "terminate non-model python: $pid $cmd"
      kill "$pid" 2>/dev/null || true
    fi
  done
else
  echo "model process is not running; skipping cleanup to avoid killing the wrong process"
fi

sleep 2

echo "=== nvidia-smi after ==="
nvidia-smi
