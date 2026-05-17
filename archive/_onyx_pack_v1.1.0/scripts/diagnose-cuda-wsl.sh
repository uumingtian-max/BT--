#!/usr/bin/env bash
set -u

echo "which nvcc:"
which nvcc || true

echo "nvcc version:"
nvcc -V || true

echo "nvidia-smi:"
nvidia-smi || true

echo "cuda paths:"
ls -ld /usr/local/cuda /usr/local/cuda/bin /usr/local/cuda/bin/nvcc /usr/include /usr/lib/x86_64-linux-gnu /usr/lib/wsl/lib 2>/dev/null || true
readlink -f /usr/local/cuda/bin/nvcc 2>/dev/null || true

echo "torch cuda:"
"$HOME/miniconda/bin/python" - <<'PY'
import torch

print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
print("device count", torch.cuda.device_count())
if torch.cuda.is_available():
    print("device", torch.cuda.get_device_name(0))
PY
