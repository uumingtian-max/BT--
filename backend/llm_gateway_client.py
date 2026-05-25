"""OpenAI-compatible LLM gateway client for BKLT 黑光.

This module lets the backend talk to local vLLM / LiteLLM / LocalAI services
through /v1/models and /v1/chat/completions without vendor SDK lock-in.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional

DEFAULT_BASE_URL = "http://127.0.0.1:8001/v1"
DEFAULT_MODEL = "nvidia/Gemma-4-26B-A4B-NVFP4"
DEFAULT_API_KEY = "local"


class LLMGatewayError(RuntimeError):
    """Raised when the OpenAI-compatible gateway is unreachable or invalid."""


@dataclass(frozen=True)
class LLMGatewayConfig:
    base_url: str = DEFAULT_BASE_URL
    api_key: str = DEFAULT_API_KEY
    model: str = DEFAULT_MODEL
    timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> "LLMGatewayConfig":
        return cls(
            base_url=os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            api_key=os.getenv("OPENAI_API_KEY", DEFAULT_API_KEY),
            model=os.getenv("AGENT_DEFAULT_MODEL", os.getenv("BKLT_MODEL_ID", DEFAULT_MODEL)),
            timeout_seconds=float(os.getenv("BKLT_LLM_TIMEOUT_SECONDS", "60")),
        )


class LLMGatewayClient:
    def __init__(self, config: Optional[LLMGatewayConfig] = None) -> None:
        self.config = config or LLMGatewayConfig.from_env()

    @property
    def base_url(self) -> str:
        return self.config.base_url.rstrip("/")

    def list_models(self) -> Dict[str, Any]:
        return self._request("GET", "/models")

    def healthcheck(self) -> Dict[str, Any]:
        data = self.list_models()
        model_ids = [item.get("id") for item in data.get("data", []) if isinstance(item, Mapping)]
        expected = self.config.model
        return {
            "ok": bool(model_ids),
            "base_url": self.base_url,
            "expected_model": expected,
            "models": model_ids,
            "model_available": expected in model_ids if model_ids else False,
        }

    def chat(
        self,
        prompt: str,
        *,
        system: str = "You are BKLT 黑光, a local AI agent workspace.",
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        result = self.chat_messages(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choices = result.get("choices") or []
        if not choices:
            raise LLMGatewayError("Gateway returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise LLMGatewayError("Gateway returned an invalid message payload")
        return content

    def chat_messages(
        self,
        messages: Iterable[Mapping[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model or self.config.model,
            "messages": list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if extra:
            payload.update(dict(extra))
        return self._request("POST", "/chat/completions", payload)

    def _request(self, method: str, path: str, payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            },
            method=method.upper(),
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMGatewayError(f"Gateway HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LLMGatewayError(f"Gateway unreachable at {url}: {exc.reason}") from exc

        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise LLMGatewayError(f"Gateway returned non-JSON response: {raw[:200]}") from exc
        if not isinstance(data, dict):
            raise LLMGatewayError("Gateway returned a non-object JSON response")
        return data


__all__ = ["LLMGatewayClient", "LLMGatewayConfig", "LLMGatewayError", "DEFAULT_BASE_URL", "DEFAULT_MODEL"]
