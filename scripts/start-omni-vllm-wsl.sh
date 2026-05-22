#!/usr/bin/env bash
# Nemotron Omni NVFP4 — WSL 原生 vLLM（推荐，勿用 Docker 跑此模型）
#
# --skip-mm-profiling：只跳过「启动时」最大分辨率 video 显存探测（避免 illegal access）
# 仍保留 limit-mm / video-pruning → BT 聊天可附图/视频/音频（Omni 多模态理解）
#
# 用法:
#   bash scripts/start-omni-vllm-wsl.sh
#   VLLM_ENFORCE_EAGER=1 bash scripts/start-omni-vllm-wsl.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="${MODEL_DIR:-/mnt/d/models/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4}"
PORT="${PORT:-8001}"
LOG="${VLLM_LOG:-/mnt/c/Users/ROG/Desktop/ai-agent-project/logs/vllm-wsl.log}"

export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-12.9}"
export PATH="${CUDA_HOME}/bin:${HOME}/miniconda/bin:${PATH:-}"
export CC="${CC:-gcc-13}"
export CXX="${CXX:-g++-13}"
export CUDAHOSTCXX="${CUDAHOSTCXX:-g++-13}"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"

PYTHON="${PYTHON:-${HOME}/miniconda/bin/python}"
if [ ! -x "$PYTHON" ]; then
  PYTHON="$(command -v python3)"
fi

mkdir -p "$(dirname "$LOG")"
: >"$LOG"

EXTRA=()
if [ "${VLLM_ENFORCE_EAGER:-0}" = "1" ]; then
  EXTRA+=(--enforce-eager)
fi

echo "[omni] model=$MODEL_DIR port=$PORT log=$LOG" | tee -a "$LOG"
MM_LIMIT="${VLLM_MM_LIMIT:-'{\"image\":1,\"video\":1,\"audio\":1}'}"
MM_MEDIA="${VLLM_MM_MEDIA:-'{\"video\":{\"fps\":1,\"num_frames\":32}}'}"

echo "[omni] skip-mm-profiling (boot only); runtime MM: image/video/audio enabled" | tee -a "$LOG"
echo "[omni] limit-mm-per-prompt=$MM_LIMIT video-pruning=${VLLM_VIDEO_PRUNING:-0.8}" | tee -a "$LOG"

exec "$PYTHON" -u -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_DIR" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --dtype auto \
  --trust-remote-code \
  --max-model-len "${VLLM_MAX_MODEL_LEN:-4096}" \
  --max-num-seqs "${VLLM_MAX_NUM_SEQS:-2}" \
  --max-num-batched-tokens 1024 \
  --gpu-memory-utilization "${VLLM_GPU_UTIL:-0.78}" \
  --skip-mm-profiling \
  --max-cudagraph-capture-size 256 \
  --limit-mm-per-prompt "$MM_LIMIT" \
  --media-io-kwargs "$MM_MEDIA" \
  --mm-processor-cache-gb 0 \
  --video-pruning-rate "${VLLM_VIDEO_PRUNING:-0.8}" \
  --allowed-local-media-path /mnt \
  "${EXTRA[@]}" \
  2>&1 | tee -a "$LOG"
