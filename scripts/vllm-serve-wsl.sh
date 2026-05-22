#!/usr/bin/env bash
# WSL Ubuntu: Miniconda + vLLM + CUDA 12.9（5090 / Nemotron NVFP4）
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sed -i 's/\r$//' "${ROOT_DIR}/ensure-wsl-ninja.sh" 2>/dev/null || true
bash "${ROOT_DIR}/ensure-wsl-ninja.sh" 2>/dev/null || true

MODEL_DIR="${MODEL_DIR:-/mnt/d/models/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4}"
PORT="${PORT:-8001}"
LOG="${VLLM_LOG:-/mnt/c/Users/ROG/Desktop/ai-agent-project/logs/vllm-wsl.log}"
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"

if [ -d /usr/local/cuda-12.9/bin ]; then
  export CUDA_HOME=/usr/local/cuda-12.9
  export PATH="/usr/local/cuda-12.9/bin:${PATH:-}"
  ln -sf /usr/local/cuda-12.9/bin/nvcc /usr/bin/nvcc 2>/dev/null || true
elif [ -d /usr/local/cuda/bin ]; then
  export CUDA_HOME=/usr/local/cuda
  export PATH="/usr/local/cuda/bin:${PATH:-}"
else
  echo "[vllm-wsl] ERROR: 需要 /usr/local/cuda-12.9（运行 scripts/install-wsl-cuda129.sh）" | tee -a "$LOG"
  exit 1
fi

export PATH="${HOME}/miniconda/bin:${HOME}/miniconda3/bin:${HOME}/.local/bin:/usr/local/bin:/usr/bin:${PATH:-}"
if [ -x /usr/bin/gcc-13 ] && [ -x /usr/bin/g++-13 ]; then
  export CC=/usr/bin/gcc-13
  export CXX=/usr/bin/g++-13
  export CUDAHOSTCXX=/usr/bin/g++-13
fi
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
export VLLM_USE_FLASHINFER_SAMPLER=0
export VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0

pick_python() {
  for candidate in \
    "$HOME/miniconda/bin/python" \
    "$HOME/miniconda3/bin/python" \
    "/home/rog/miniconda/bin/python"; do
    if [ -x "$candidate" ]; then
      echo "$candidate"
      return 0
    fi
  done
  command -v python3
}

PYTHON="$(pick_python || true)"
if [ -z "$PYTHON" ]; then
  echo "[vllm-wsl] ERROR: 未找到 Python" | tee -a "$LOG"
  exit 1
fi

mkdir -p "$(dirname "$LOG")"
echo "[vllm-wsl] PYTHON=$PYTHON CUDA_HOME=$CUDA_HOME" | tee -a "$LOG"
echo "[vllm-wsl] MODEL_DIR=$MODEL_DIR PORT=$PORT" | tee -a "$LOG"

if ! command -v ninja >/dev/null 2>&1; then
  "$PYTHON" -m pip install -U ninja cmake
fi
if ! "$PYTHON" -c "import vllm" 2>/dev/null; then
  echo "[vllm-wsl] installing vllm …" | tee -a "$LOG"
  "$PYTHON" -m pip install -U pip wheel vllm
fi

EXTRA_ARGS=(--trust-remote-code)

echo "[vllm-wsl] starting api_server …" | tee -a "$LOG"
exec "$PYTHON" -u -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_DIR" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --dtype auto \
  --max-model-len "${VLLM_MAX_MODEL_LEN:-4096}" \
  --max-num-batched-tokens 1024 \
  --gpu-memory-utilization "${VLLM_GPU_UTIL:-0.78}" \
  --max-num-seqs 4 \
  --skip-mm-profiling \
  --max-cudagraph-capture-size 256 \
  --limit-mm-per-prompt '{"image":1,"video":1,"audio":1}' \
  --media-io-kwargs '{"video":{"fps":1,"num_frames":32}}' \
  --mm-processor-cache-gb 0 \
  --video-pruning-rate 0.8 \
  --allowed-local-media-path /mnt \
  --no-enable-log-requests \
  --disable-log-stats \
  "${EXTRA_ARGS[@]}" >>"$LOG" 2>&1
