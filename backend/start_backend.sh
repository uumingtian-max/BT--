#!/bin/bash
echo "=== BT-Blacklight 后端启动 ==="
pip install pyyaml schedule openai cryptography
if ! curl -s http://localhost:30000/v1/models >/dev/null; then
    echo "请先启动 SGLang: cd ../sglang && ./start_sglang_30B.sh"
    exit 1
fi
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
echo "后端: http://localhost:8000"
