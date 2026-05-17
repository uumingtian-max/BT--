#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/mnt/c/Users/ROG/Desktop/ai-agent-project"
LOG="$PROJECT_DIR/vllm-gemma.log"
PID_FILE="$PROJECT_DIR/vllm-gemma.pid"

export CUDA_HOME=/usr
export PATH=/usr/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib/wsl/lib:/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export VLLM_USE_FLASHINFER_SAMPLER=0
export VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0

pkill -f "vllm.entrypoints.openai.api_server" 2>/dev/null || true

PYTHON="$HOME/miniconda/bin/python"
: > "$LOG"

nohup "$PYTHON" -m vllm.entrypoints.openai.api_server \
  --model /mnt/d/models/Gemma-4-26B-A4B-NVFP4 \
  --quantization fp4 \
  --dtype bfloat16 \
  --max-model-len 32768 \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.88 \
  --max-num-seqs 32 \
  --generation-config vllm \
  --no-enable-log-requests \
  --disable-log-stats \
  --host 0.0.0.0 \
  --port 8001 \
  > "$LOG" 2>&1 &

echo "$!" > "$PID_FILE"
sleep 5

echo "PID=$(cat "$PID_FILE")"
echo "LOG=$LOG"
tail -n 60 "$LOG"
