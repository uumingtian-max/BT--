"""Check BKLT 黑光 GPU/NPU/API OpenAI-compatible LLM routes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.llm_gateway_client import LLMGatewayClient, LLMGatewayConfig, LLMGatewayError
from backend.llm_router import LLMRouter


def main() -> int:
    parser = argparse.ArgumentParser(description="Check BKLT LLM gateway/routes")
    parser.add_argument("--route", choices=["gpu", "npu", "api", "auto", "direct"], default=os.getenv("BKLT_LLM_DEFAULT_ROUTE", "gpu"))
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8001/v1"), help="Used only with --route direct")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", "local"), help="Used only with --route direct")
    parser.add_argument("--model", default=os.getenv("AGENT_DEFAULT_MODEL", os.getenv("BKLT_MODEL_ID", "nvidia/Gemma-4-26B-A4B-NVFP4")), help="Used only with --route direct")
    parser.add_argument("--prompt", default="用一句中文回复：BKLT 黑光模型网关正常。")
    parser.add_argument("--timeout", type=float, default=float(os.getenv("BKLT_LLM_TIMEOUT_SECONDS", "60")))
    parser.add_argument("--skip-chat", action="store_true", help="Only check /models")
    args = parser.parse_args()

    try:
        if args.route == "direct":
            client = LLMGatewayClient(LLMGatewayConfig(args.base_url.rstrip("/"), args.api_key, args.model, args.timeout))
            health = client.healthcheck()
            print(json.dumps(health, ensure_ascii=False, indent=2))
            if not args.skip_chat:
                print("\n[BKLT] Chat completion OK:")
                print(client.chat(args.prompt, max_tokens=80))
            return 0

        router = LLMRouter.from_env()
        health = router.healthcheck(args.route)
        print(json.dumps(health, ensure_ascii=False, indent=2))
        if not health.get("ok"):
            print(f"[BKLT] Route check failed: {args.route}", file=sys.stderr)
            return 2
        if not args.skip_chat:
            print("\n[BKLT] Chat completion OK:")
            print(router.chat(args.prompt, route=args.route, max_tokens=80))
    except LLMGatewayError as exc:
        print(f"[BKLT] LLM gateway check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
