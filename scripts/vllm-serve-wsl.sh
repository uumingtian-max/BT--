#!/usr/bin/env bash
# 兼容入口：委托给 start-omni-vllm-wsl.sh（5090 / Nemotron Omni NVFP4）
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${ROOT_DIR}/start-omni-vllm-wsl.sh"
