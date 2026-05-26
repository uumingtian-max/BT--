"""双引擎：API（inferaichat / Opus）+ GPU（本地 Nemotron Omni）同时启用。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

from mm_openai_payload import attachment_requires_vllm, normalize_attachments, omni_mm_enabled

RouteName = Literal["gpu", "api"]


@dataclass(frozen=True)
class ResolvedEndpoint:
    route: RouteName
    base_url: str
    api_key: str
    model: str


def dual_engine_enabled() -> bool:
    return os.environ.get("BKLT_DUAL_ENGINE", "1").strip().lower() not in (
        "0",
        "false",
        "off",
        "no",
    )


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _route_gpu() -> ResolvedEndpoint | None:
    base = _env("GPU_OPENAI_BASE_URL")
    model = _env("GPU_MODEL") or _env("BKLT_OMNI_MODEL") or _env("ORCH_VISION_MODEL")
    if not base or not model:
        return None
    return ResolvedEndpoint(
        route="gpu",
        base_url=base.rstrip("/"),
        api_key=_env("GPU_OPENAI_API_KEY", "local"),
        model=model,
    )


def _route_api() -> ResolvedEndpoint | None:
    base = _env("API_OPENAI_BASE_URL") or _env("OPENAI_BASE_URL")
    model = _env("API_MODEL") or _env("LOCKED_MODEL_ID") or _env("AGENT_DEFAULT_MODEL")
    key = _env("API_OPENAI_API_KEY") or _env("OPENAI_API_KEY")
    if not base or not model:
        return None
    return ResolvedEndpoint(
        route="api",
        base_url=base.rstrip("/"),
        api_key=key or "local",
        model=model,
    )


def _messages_need_gpu(messages: list[dict[str, Any]]) -> bool:
    if not omni_mm_enabled():
        return False
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        if m.get("role") != "user":
            continue
        if normalize_attachments(m.get("attachments")):  # type: ignore[arg-type]
            return True
        content = m.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") not in (None, "text"):
                    return True
    return False


def _model_prefers_gpu(model: str) -> bool:
    mid = (model or "").lower()
    gpu_markers = (
        _env("GPU_MODEL").lower(),
        _env("BKLT_OMNI_MODEL").lower(),
        _env("ORCH_VISION_MODEL").lower(),
        "nemotron",
        "omni",
        "gemma",
    )
    return any(m and m in mid for m in gpu_markers if m)


def _model_prefers_api(model: str) -> bool:
    mid = (model or "").lower()
    api_markers = (
        _env("API_MODEL").lower(),
        _env("LOCKED_MODEL_ID").lower(),
        "claude",
        "opus",
        "gpt",
    )
    return any(m and m in mid for m in api_markers if m)


def resolve_openai_endpoint(
    messages: list[dict[str, Any]],
    model: str,
    *,
    attachments: list[dict[str, Any]] | None = None,
) -> ResolvedEndpoint:
    """选择本次请求的 OpenAI 兼容网关。"""
    gpu = _route_gpu()
    api = _route_api()

    if not dual_engine_enabled():
        from agent_runtime import get_runtime

        rt = get_runtime()
        return ResolvedEndpoint(
            route="api",
            base_url=(rt.openai_base_url or "").rstrip("/"),
            api_key=rt.openai_api_key or "local",
            model=(model or rt.default_chat_model or "").strip(),
        )

    need_gpu = _messages_need_gpu(messages) or attachment_requires_vllm(attachments)

    if need_gpu and gpu:
        return ResolvedEndpoint(
            route=gpu.route,
            base_url=gpu.base_url,
            api_key=gpu.api_key,
            model=gpu.model,
        )

    if _model_prefers_gpu(model) and gpu:
        return gpu

    default_route = _env("BKLT_LLM_DEFAULT_ROUTE", "api").lower()
    if default_route == "gpu" and gpu:
        return ResolvedEndpoint(gpu.route, gpu.base_url, gpu.api_key, model or gpu.model)
    if api:
        return ResolvedEndpoint(
            route=api.route,
            base_url=api.base_url,
            api_key=api.api_key,
            model=model or api.model,
        )
    if gpu:
        return ResolvedEndpoint(gpu.route, gpu.base_url, gpu.api_key, model or gpu.model)
    raise RuntimeError("双引擎已开启但未配置 GPU_OPENAI_BASE_URL / API_OPENAI_BASE_URL")


def dual_engine_status() -> dict[str, Any]:
    from llm_router import get_default_router

    gpu = _route_gpu()
    api = _route_api()
    out: dict[str, Any] = {
        "ok": False,
        "dual_engine": dual_engine_enabled(),
        "default_route": _env("BKLT_LLM_DEFAULT_ROUTE", "api"),
        "fallback_order": _env("BKLT_LLM_FALLBACK_ORDER", "api,gpu"),
        "policy": "纯文字→API(Opus)；附件/图音视频→GPU(Nemotron)",
        "routes": {},
    }
    router = get_default_router()
    if gpu:
        try:
            out["routes"]["gpu"] = {
                "base_url": gpu.base_url,
                "model": gpu.model,
                "api_key_set": bool(gpu.api_key),
                **router.healthcheck("gpu"),
            }
        except Exception as exc:
            out["routes"]["gpu"] = {"ok": False, "base_url": gpu.base_url, "error": str(exc)}
    if api:
        try:
            out["routes"]["api"] = {
                "base_url": api.base_url,
                "model": api.model,
                "api_key_set": bool(api.api_key and api.api_key != "local"),
                **router.healthcheck("api"),
            }
        except Exception as exc:
            out["routes"]["api"] = {"ok": False, "base_url": api.base_url, "error": str(exc)}
    out["ok"] = any(
        isinstance(r, dict) and r.get("ok") for r in out.get("routes", {}).values()
    )
    return out
