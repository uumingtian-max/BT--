#!/usr/bin/env bash
# WSL Ubuntu: 安装依赖并启动 vLLM（由 ensure-vllm.ps1 调用）
MODEL_DIR="${MODEL_DIR:-/mnt/d/models/Gemma-4-26B-A4B-NVFP4}"
PORT="${PORT:-8001}"
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"

if ! command -v pip3 >/dev/null 2>&1; then
  echo "[vllm-wsl] installing python3-pip..."
  export DEBIAN_FRONTEND=noninteractive
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-pip python3-venv
fi

if ! python3 -c "import vllm" 2>/dev/null; then
  echo "[vllm-wsl] installing vllm (may take several minutes)..."
  python3 -m pip install --user -U pip wheel
  python3 -m pip install --user -U vllm
fi

export PATH="$HOME/.local/bin:$PATH"
echo "[vllm-wsl] starting server on port $PORT model=$MODEL_DIR"
exec python3 -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_DIR" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90
