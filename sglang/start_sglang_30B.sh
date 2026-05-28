#!/bin/bash
python -m sglang.launch_server \
  --model-path /path/to/your/30B-model \
  --port 30000 \
  --tp-size 2 \
  --dtype bfloat16 \
  --mem-fraction 0.85 \
  --context-window 128000 \
  --enable-flashinfer \
  --trust-remote-code \
  --max-prefill-tokens 16384
echo "SGLang: http://localhost:30000/v1"
