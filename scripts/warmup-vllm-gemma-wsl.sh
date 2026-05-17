#!/usr/bin/env bash
set -euo pipefail

MODEL="/mnt/d/models/Gemma-4-26B-A4B-NVFP4"
BASE_URL="http://127.0.0.1:8001"

echo "[warmup] waiting for vLLM..."
for _ in $(seq 1 120); do
  if curl -fsS "$BASE_URL/v1/models" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

curl -fsS "$BASE_URL/v1/models" >/dev/null
echo "[warmup] gateway ready"

send_chat() {
  local content="$1"
  local max_tokens="$2"
  curl -fsS "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d @- >/dev/null <<EOF
{"model":"$MODEL","messages":[{"role":"system","content":"You are a concise local assistant."},{"role":"user","content":"$content"}],"max_tokens":$max_tokens,"temperature":0.1}
EOF
}

send_chat "Say OK." 16
send_chat "Give a short two bullet checklist for checking a local AI service." 80

echo "[warmup] completed"
