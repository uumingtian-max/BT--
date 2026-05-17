"""
调用 NVIDIA Integrate API（OpenAI 兼容 /v1/chat/completions）。

用法（不要把 key 写进文件或提交 Git）：
  set NVIDIA_API_KEY=nvapi-你的密钥
  python scripts/nvidia_integrate_chat_example.py

与 backend 对齐（backend/.env）：
  LLM_BACKEND=openai_compatible
  OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
  OPENAI_API_KEY=同上
  AGENT_DEFAULT_MODEL=meta/llama-4-maverick-17b-128e-instruct
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
STREAM = False


def main() -> int:
    api_key = (os.environ.get("NVIDIA_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        print("请设置环境变量 NVIDIA_API_KEY 或 OPENAI_API_KEY。", file=sys.stderr)
        return 1

    model = os.environ.get("NVIDIA_MODEL", "meta/llama-4-maverick-17b-128e-instruct")
    user_text = (os.environ.get("NVIDIA_PROMPT") or "用一句话介绍你自己。").strip()
    if not user_text:
        print("用户消息不能为空；请设置 NVIDIA_PROMPT 或改脚本默认值。", file=sys.stderr)
        return 1

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_text}],
        "max_tokens": 512,
        "temperature": 1.0,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "stream": STREAM,
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if STREAM else "application/json",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(INVOKE_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {err}", file=sys.stderr)
        return 1

    if STREAM:
        print(body)
    else:
        print(json.dumps(json.loads(body), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
