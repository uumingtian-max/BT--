"""
Pluggable LLM transport: not tied to Ollama.

- ollama: native /api/chat (default, unchanged behavior).
- openai_compatible: POST {OPENAI_BASE_URL}/chat/completions — works with
  vLLM, LiteLLM, LocalAI, your own FastAPI shim, etc., as long as it follows
  the OpenAI chat schema.

性能优化：使用持久化 httpx.AsyncClient 连接池，避免每次 LLM 调用都重建 TCP 连接。
"""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, AsyncIterator

import httpx

from agent_runtime import get_runtime
from ollama_pins import maybe_prepare_ollama_model, maybe_release_ollama_model, ollama_chat_body


# ---------------------------------------------------------------------------
# 持久化 HTTP 连接池
# 每次 LLM 调用重建 AsyncClient 会触发 TCP 握手，本机 Ollama/vLLM 下每次额外
# 开销约 5-30ms。改用模块级共享客户端后连接可复用，流式请求延迟明显降低。
# ---------------------------------------------------------------------------

_async_client: httpx.AsyncClient | None = None
_async_client_lock = asyncio.Lock()
_sync_client: httpx.Client | None = None
_sync_client_lock = threading.Lock()


def _make_limits() -> httpx.Limits:
    return httpx.Limits(
        max_connections=20,
        max_keepalive_connections=10,
        keepalive_expiry=30.0,
    )


async def _get_async_client() -> httpx.AsyncClient:
    """返回共享 AsyncClient，按需创建（异步安全）。"""
    global _async_client
    async with _async_client_lock:
        if _async_client is None or _async_client.is_closed:
            _async_client = httpx.AsyncClient(
                limits=_make_limits(),
                timeout=httpx.Timeout(connect=60.0, read=None, write=60.0, pool=5.0),
            )
    return _async_client


def _get_sync_client() -> httpx.Client:
    """返回共享同步 Client（线程安全）。"""
    global _sync_client
    with _sync_client_lock:
        if _sync_client is None or _sync_client.is_closed:
            _sync_client = httpx.Client(
                limits=_make_limits(),
                timeout=httpx.Timeout(connect=60.0, read=None, write=60.0, pool=5.0),
            )
    return _sync_client


async def close_shared_clients() -> None:
    """应用关闭时调用，优雅释放连接池。在 main.py lifespan yield 之后调用。"""
    global _async_client, _sync_client
    async with _async_client_lock:
        if _async_client is not None and not _async_client.is_closed:
            await _async_client.aclose()
        _async_client = None
    with _sync_client_lock:
        if _sync_client is not None and not _sync_client.is_closed:
            _sync_client.close()
        _sync_client = None


# ---------------------------------------------------------------------------
# Helper utilities (unchanged)
# ---------------------------------------------------------------------------


def _ollama_connection_message(url: str, exc: Exception) -> str:
    return (
        f"无法连接 Ollama（{url}）：{exc}。"
        "请先启动 Ollama：托盘图标、运行 ollama serve，或重新打开 BT（黑光）（会自动尝试启动）。"
        "安装：https://ollama.com"
    )


def _ollama_bad_route_message(url: str, status_code: int, error_text: str = "") -> str:
    if status_code == 404:
        lowered = (error_text or "").lower()
        fallback = error_text or "model not found"
        if "model" in lowered and ("not found" in lowered or "不存在" in error_text):
            return (
                f"当前选中的模型在 {url} 对应的 Ollama 实例里不可用：{fallback}。"
                "请换一个能用的模型，或先确认该实例已经拉起这个模型。"
            )
        return (
            f"请求 {url} 返回 404：该地址没有可用的对话接口 /api/chat。"
            "请确认本机已安装并启动较新的 Ollama，且当前 11434 确实是 Ollama 本体；"
            "若你实际用的是 LM Studio、vLLM 等 OpenAI 兼容网关，请设置 LLM_BACKEND=openai_compatible 与 OPENAI_BASE_URL，并重启本后端。"
        )
    return f"Ollama 请求失败 HTTP {status_code}：{url}"


def _ollama_request_timeout(total_sec: float) -> httpx.Timeout:
    c = min(60.0, max(10.0, float(total_sec)))
    return httpx.Timeout(connect=c, read=None, write=c, pool=5.0)


def _streaming_http_timeout(total_sec: float) -> httpx.Timeout:
    c = min(60.0, max(10.0, float(total_sec)))
    return httpx.Timeout(connect=c, read=None, write=c, pool=5.0)


def _ollama_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return messages


def _ollama_chat_options(temperature: float) -> dict[str, Any]:
    rt = get_runtime()
    opts: dict[str, Any] = {"temperature": temperature}
    if rt.ollama_num_ctx > 0:
        opts["num_ctx"] = int(rt.ollama_num_ctx)
    return opts


def _openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from mm_openai_payload import apply_multimodal_to_messages

    merged = apply_multimodal_to_messages(messages)
    out: list[dict[str, Any]] = []
    for m in merged:
        if m.get("content") is None:
            continue
        out.append({"role": m["role"], "content": m.get("content", "")})
    return out


def _openai_chat_url_headers_body(
    rt: Any,
    messages: list[dict[str, Any]],
    model: str,
    *,
    temperature: float,
    stream: bool,
) -> tuple[str, dict[str, str], dict[str, Any]]:
    base = rt.openai_base_url.rstrip("/")
    if not base:
        raise RuntimeError("LLM_BACKEND=openai_compatible 但未设置 OPENAI_BASE_URL（例如 http://127.0.0.1:8000/v1）")
    url = base + "/chat/completions"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if rt.openai_api_key:
        headers["Authorization"] = f"Bearer {rt.openai_api_key}"
    body: dict[str, Any] = {
        "model": model,
        "messages": _openai_messages(messages),
        "temperature": temperature,
        "stream": stream,
    }
    return url, headers, body


def _openai_non_stream_content(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message") or {}
    return (msg.get("content") or "").strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def chat_complete_sync(
    messages: list[dict[str, Any]],
    model: str,
    *,
    temperature: float = 0.1,
    http_timeout_sec: float | None = None,
) -> str:
    rt = get_runtime()
    timeout_val = float(rt.ollama_timeout_sec)
    if http_timeout_sec is not None:
        timeout_val = min(timeout_val, max(5.0, float(http_timeout_sec)))

    if rt.llm_backend == "openai_compatible":
        url, headers, body = _openai_chat_url_headers_body(rt, messages, model, temperature=temperature, stream=False)
        client = _get_sync_client()
        resp = client.post(url, headers=headers, json=body, timeout=timeout_val)
        resp.raise_for_status()
        return _openai_non_stream_content(resp.json())

    url = rt.ollama_chat_url()
    maybe_prepare_ollama_model(model)
    try:
        client = _get_sync_client()
        resp = client.post(
            url,
            json=ollama_chat_body(
                model,
                _ollama_messages(messages),
                stream=False,
                options=_ollama_chat_options(temperature),
            ),
            timeout=_ollama_request_timeout(timeout_val),
        )
        error_text = resp.text
        if resp.status_code == 404:
            raise RuntimeError(_ollama_bad_route_message(url, 404, error_text))
        resp.raise_for_status()
        data = resp.json()
    except httpx.ConnectError as e:
        raise RuntimeError(_ollama_connection_message(rt.ollama_base, e)) from e
    finally:
        maybe_release_ollama_model(model)
    return (data.get("message") or {}).get("content", "") or ""


async def chat_complete_async(
    messages: list[dict[str, Any]],
    model: str,
    *,
    temperature: float = 0.1,
) -> str:
    rt = get_runtime()
    timeout = rt.ollama_timeout_sec

    if rt.llm_backend == "openai_compatible":
        url, headers, body = _openai_chat_url_headers_body(rt, messages, model, temperature=temperature, stream=False)
        client = await _get_async_client()
        resp = await client.post(url, headers=headers, json=body, timeout=float(timeout))
        resp.raise_for_status()
        return _openai_non_stream_content(resp.json())

    url = rt.ollama_chat_url()
    maybe_prepare_ollama_model(model)
    try:
        client = await _get_async_client()
        resp = await client.post(
            url,
            json=ollama_chat_body(
                model,
                _ollama_messages(messages),
                stream=False,
                options=_ollama_chat_options(temperature),
            ),
            timeout=_ollama_request_timeout(float(timeout)),
        )
        error_text = resp.text
        if resp.status_code == 404:
            raise RuntimeError(_ollama_bad_route_message(url, 404, error_text))
        resp.raise_for_status()
        data = resp.json()
    except httpx.ConnectError as e:
        raise RuntimeError(_ollama_connection_message(rt.ollama_base, e)) from e
    finally:
        maybe_release_ollama_model(model)
    return (data.get("message") or {}).get("content", "") or ""


async def chat_stream_async(
    messages: list[dict[str, Any]],
    model: str,
    *,
    temperature: float = 0.1,
) -> AsyncIterator[str]:
    rt = get_runtime()
    timeout = rt.ollama_timeout_sec

    if rt.llm_backend == "openai_compatible":
        url, headers, body = _openai_chat_url_headers_body(rt, messages, model, temperature=temperature, stream=True)
        client = await _get_async_client()
        async with client.stream(
            "POST",
            url,
            headers=headers,
            json=body,
            timeout=_streaming_http_timeout(float(timeout)),
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                choices = obj.get("choices") or []
                if not choices:
                    continue
                choice0 = choices[0]
                delta = choice0.get("delta") or {}
                chunk = delta.get("content") or ""
                if chunk:
                    yield chunk
                if choice0.get("finish_reason") or obj.get("done"):
                    break
        return

    url = rt.ollama_chat_url()
    maybe_prepare_ollama_model(model)
    try:
        client = await _get_async_client()
        async with client.stream(
            "POST",
            url,
            json=ollama_chat_body(
                model,
                _ollama_messages(messages),
                stream=True,
                options=_ollama_chat_options(temperature),
            ),
            timeout=_streaming_http_timeout(float(timeout)),
        ) as resp:
            if resp.status_code == 404:
                error_text = (await resp.aread()).decode("utf-8", errors="ignore")
                raise RuntimeError(_ollama_bad_route_message(url, 404, error_text))
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "message" in data:
                    yield data["message"].get("content", "") or ""
                if data.get("done"):
                    return
    except httpx.ConnectError as e:
        raise RuntimeError(_ollama_connection_message(rt.ollama_base, e)) from e
    finally:
        maybe_release_ollama_model(model)
