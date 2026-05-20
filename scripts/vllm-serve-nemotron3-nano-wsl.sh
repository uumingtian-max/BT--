#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="${MODEL_DIR:-/mnt/d/models/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4}"
PORT="${PORT:-8001}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-4}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4}"
PARSER_PATH="${PARSER_PATH:-/tmp/nano_v3_reasoning_parser.py}"

export PATH="$HOME/.local/bin:$PATH"
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
export VLLM_USE_FLASHINFER_MOE_FP4="${VLLM_USE_FLASHINFER_MOE_FP4:-1}"
export VLLM_FLASHINFER_MOE_BACKEND="${VLLM_FLASHINFER_MOE_BACKEND:-throughput}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[vllm-nemotron] python3 not found. Please install Ubuntu/WSL python3 first."
  exit 1
fi

if ! command -v pip3 >/dev/null 2>&1; then
  echo "[vllm-nemotron] installing python3-pip..."
  export DEBIAN_FRONTEND=noninteractive
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-pip python3-venv wget
fi

if ! command -v wget >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq wget
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "[vllm-nemotron] WARNING: nvidia-smi not found in WSL. GPU/vLLM may not work."
else
  nvidia-smi
fi

if ! python3 -c "import vllm" >/dev/null 2>&1; then
  echo "[vllm-nemotron] installing vLLM >= 0.12.0..."
  python3 -m pip install --user -U pip wheel
  python3 -m pip install --user -U "vllm>=0.12.0"
fi

if [ ! -f "$PARSER_PATH" ]; then
  echo "[vllm-nemotron] downloading nano_v3_reasoning_parser.py..."
  wget -O "$PARSER_PATH" "https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4/resolve/main/nano_v3_reasoning_parser.py"
fi

echo "[vllm-nemotron] model=$MODEL_DIR"
echo "[vllm-nemotron] served-model-name=$SERVED_MODEL_NAME"
echo "[vllm-nemotron] port=$PORT max_model_len=$MAX_MODEL_LEN max_num_seqs=$MAX_NUM_SEQS"

exec python3 -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_DIR" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --max-num-seqs "$MAX_NUM_SEQS" \
  --tensor-parallel-size 1 \
  --max-model-len "$MAX_MODEL_LEN" \
  --trust-remote-code \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser-plugin "$PARSER_PATH" \
  --reasoning-parser nano_v3 \
  --kv-cache-dtype fp8 \
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
