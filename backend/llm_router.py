"""Three-route LLM router for BKLT 黑光.

Routes:
- gpu: local GPU model OpenAI-compatible API
- npu: local NPU model OpenAI-compatible API
- api: external/cloud OpenAI-compatible API
- auto: try configured routes in order until one succeeds
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from llm_gateway_client import LLMGatewayClient, LLMGatewayConfig, LLMGatewayError

RouteName = str
VALID_ROUTES = ("gpu", "npu", "api")


@dataclass(frozen=True)
class LLMRoute:
    name: RouteName
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 60.0

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.model)

    def client(self) -> LLMGatewayClient:
        return LLMGatewayClient(
            LLMGatewayConfig(
                base_url=self.base_url.rstrip("/"),
                api_key=self.api_key or "local",
                model=self.model,
                timeout_seconds=self.timeout_seconds,
            )
        )


class LLMRouter:
    def __init__(self, routes: Mapping[RouteName, LLMRoute], fallback_order: Sequence[RouteName]) -> None:
        self.routes = dict(routes)
        self.fallback_order = list(fallback_order)

    @classmethod
    def from_env(cls) -> "LLMRouter":
        timeout = float(os.getenv("BKLT_LLM_TIMEOUT_SECONDS", "60"))
        legacy_base = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8001/v1")
        legacy_key = os.getenv("OPENAI_API_KEY", "local")
        legacy_model = os.getenv("AGENT_DEFAULT_MODEL", os.getenv("BKLT_MODEL_ID", "nvidia/Gemma-4-26B-A4B-NVFP4"))
        routes = {
            "gpu": LLMRoute("gpu", os.getenv("GPU_OPENAI_BASE_URL", legacy_base), os.getenv("GPU_OPENAI_API_KEY", legacy_key), os.getenv("GPU_MODEL", legacy_model), timeout),
            "npu": LLMRoute("npu", os.getenv("NPU_OPENAI_BASE_URL", "http://127.0.0.1:8002/v1"), os.getenv("NPU_OPENAI_API_KEY", "local"), os.getenv("NPU_MODEL", ""), timeout),
            "api": LLMRoute("api", os.getenv("API_OPENAI_BASE_URL", ""), os.getenv("API_OPENAI_API_KEY", ""), os.getenv("API_MODEL", ""), timeout),
        }
        return cls(routes, parse_fallback_order(os.getenv("BKLT_LLM_FALLBACK_ORDER", "gpu,npu,api")))

    def get_route(self, route: RouteName) -> LLMRoute:
        if route not in self.routes:
            raise LLMGatewayError(f"Unknown LLM route: {route}. Valid routes: {', '.join(self.routes)}")
        selected = self.routes[route]
        if not selected.enabled:
            raise LLMGatewayError(f"LLM route is not configured: {route}")
        return selected

    def client(self, route: RouteName = "gpu") -> LLMGatewayClient:
        return self.get_route(route).client()

    def healthcheck(self, route: RouteName = "auto") -> Dict[str, Any]:
        if route == "auto":
            results: Dict[str, Any] = {}
            ok = False
            for name in self.fallback_order:
                try:
                    results[name] = self.healthcheck(name)
                    ok = ok or bool(results[name].get("ok"))
                except Exception as exc:
                    results[name] = {"ok": False, "route": name, "error": str(exc)}
            return {"ok": ok, "mode": "auto", "fallback_order": self.fallback_order, "routes": results}
        selected = self.get_route(route)
        data = selected.client().healthcheck()
        data["route"] = selected.name
        return data

    def chat(self, prompt: str, *, route: RouteName = "auto", system: str = "You are BKLT 黑光, a local AI agent workspace.", temperature: float = 0.2, max_tokens: int = 512) -> str:
        if route != "auto":
            return self.client(route).chat(prompt, system=system, temperature=temperature, max_tokens=max_tokens)
        errors: List[str] = []
        for name in self.fallback_order:
            try:
                return self.client(name).chat(prompt, system=system, temperature=temperature, max_tokens=max_tokens)
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        raise LLMGatewayError("All LLM routes failed: " + " | ".join(errors))

    def chat_messages(self, messages: Iterable[Mapping[str, str]], *, route: RouteName = "auto", temperature: float = 0.2, max_tokens: int = 512, extra: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        if route != "auto":
            return self.client(route).chat_messages(messages, temperature=temperature, max_tokens=max_tokens, extra=extra)
        errors: List[str] = []
        for name in self.fallback_order:
            try:
                return self.client(name).chat_messages(messages, temperature=temperature, max_tokens=max_tokens, extra=extra)
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        raise LLMGatewayError("All LLM routes failed: " + " | ".join(errors))


def parse_fallback_order(raw: str) -> List[RouteName]:
    order = [item.strip().lower() for item in raw.split(",") if item.strip()]
    cleaned = [item for item in order if item in VALID_ROUTES]
    return cleaned or ["gpu", "npu", "api"]


def get_default_router() -> LLMRouter:
    return LLMRouter.from_env()


__all__ = ["LLMRoute", "LLMRouter", "RouteName", "VALID_ROUTES", "get_default_router", "parse_fallback_order"]
