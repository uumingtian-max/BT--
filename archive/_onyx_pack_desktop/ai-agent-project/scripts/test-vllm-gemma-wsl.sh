#!/usr/bin/env bash
set -euo pipefail

curl -sS http://127.0.0.1:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/d/models/Gemma-4-26B-A4B-NVFP4",
    "messages": [
      {"role": "user", "content": "用一句中文回答：你已经启动了吗？"}
    ],
    "max_tokens": 32,
    "temperature": 0
  }'
