#!/usr/bin/env bash
set -euo pipefail

"$HOME/miniconda/bin/python" - <<'PY'
import sys
import vllm

print(sys.executable)
print(vllm.__version__)
PY
