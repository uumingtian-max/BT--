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
import time
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
        # pool_timeout 默认 5s 在并发请求时太容易触发 PoolTimeout，改为 30s
    )


async def _get_async_client() -> httpx.AsyncClient:
    """返回共享 AsyncClient，按需创建（异步安全）。"""
    global _async_client
    async with _async_client_lock:
        if _async_client is None or _async_client.is_closed:
            _async_client = httpx.AsyncClient(
                limits=_make_limits(),
                timeout=httpx.Timeout(connect=60.0, read=None, write=60.0, pool=30.0),
            )
    return _async_client


def _get_sync_client() -> httpx.Client:
    """返回共享同步 Client（线程安全）。"""
    global _sync_client
    with _sync_client_lock:
        if _sync_client is None or _sync_client.is_closed:
            _sync_client = httpx.Client(
                limits=_make_limits(),
                timeout=httpx.Timeout(connect=60.0, read=None, write=60.0, pool=30.0),
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


_OPENAI_RETRYABLE = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
)
_OPENAI_MAX_RETRIES = 3
_OPENAI_RETRY_DELAYS = (1.0, 3.0, 8.0)


def _openai_transient_error_message(url: str, exc: Exception) -> str:
    return f"连接 LLM 网关（{url}）失败：{exc}。已重试 3 次，请检查网络或 OPENAI_BASE_URL 配置。"


def _openai_timeout_message(url: str, exc: Exception) -> str:
    return (
        f"LLM 网关（{url}）响应超时：{exc}。"
        "可调大 OLLAMA_TIMEOUT_SEC / BKLT_LLM_TIMEOUT_SECONDS 环境变量，或检查网络质量。"
    )


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


def _extract_text_from_content(content: Any) -> str:
    """Claude API 可能返回 content 为数组（含 tool_use 块），提取纯文本。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                parts.append(block.get("text") or "")
            # tool_use / tool_result 块直接丢弃，不进消息历史
        return " ".join(p for p in parts if p).strip()
    return str(content) if content is not None else ""


def _sanitize_content_for_api(content: Any) -> Any:
    """发给 API 前净化 content：数组里的 tool_use/tool_result 块会触发 Claude 校验错误。

    - 纯文本 → 原样
    - 数组有 image_url/video_url/input_audio → 保留媒体块，剥掉 tool 块
    - 数组只有 text/tool 块 → 合并成纯字符串
    """
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content) if content is not None else ""
    _TOOL_TYPES = {"tool_use", "tool_result"}
    _MEDIA_TYPES = {"image_url", "video_url", "input_audio"}
    filtered: list[dict[str, Any]] = [b for b in content if isinstance(b, dict) and b.get("type") not in _TOOL_TYPES]
    if not filtered:
        return ""
    has_media = any(b.get("type") in _MEDIA_TYPES for b in filtered)
    if has_media:
        return filtered
    # 只剩 text 块，合并为字符串
    return " ".join((b.get("text") or "") for b in filtered if b.get("type") == "text").strip()


def _openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from mm_openai_payload import apply_multimodal_to_messages

    merged = apply_multimodal_to_messages(messages)
    out: list[dict[str, Any]] = []
    for m in merged:
        raw_content = m.get("content")
        if raw_content is None:
            continue
        clean = _sanitize_content_for_api(raw_content)
        if clean == "" and m.get("role") == "assistant":
            # assistant 消息内容为空（全是 tool 块）时跳过，避免空消息报错
            continue
        out.append({"role": m["role"], "content": clean})
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
    return _extract_text_from_content(msg.get("content")).strip()


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
        req_timeout = httpx.Timeout(connect=60.0, read=timeout_val, write=60.0, pool=30.0)
        last_exc: Exception | None = None
        for attempt in range(_OPENAI_MAX_RETRIES):
            try:
                resp = client.post(url, headers=headers, json=body, timeout=req_timeout)
                resp.raise_for_status()
                return _openai_non_stream_content(resp.json())
            except httpx.ReadTimeout as e:
                raise RuntimeError(_openai_timeout_message(url, e)) from e
            except _OPENAI_RETRYABLE as e:
                last_exc = e
                if attempt < _OPENAI_MAX_RETRIES - 1:
                    time.sleep(_OPENAI_RETRY_DELAYS[attempt])
        raise RuntimeError(_openai_transient_error_message(url, last_exc)) from last_exc

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
        req_timeout = httpx.Timeout(connect=60.0, read=float(timeout), write=60.0, pool=30.0)
        last_exc: Exception | None = None
        for attempt in range(_OPENAI_MAX_RETRIES):
            try:
                resp = await client.post(url, headers=headers, json=body, timeout=req_timeout)
                resp.raise_for_status()
                return _openai_non_stream_content(resp.json())
            except httpx.ReadTimeout as e:
                raise RuntimeError(_openai_timeout_message(url, e)) from e
            except _OPENAI_RETRYABLE as e:
                last_exc = e
                if attempt < _OPENAI_MAX_RETRIES - 1:
                    await asyncio.sleep(_OPENAI_RETRY_DELAYS[attempt])
        raise RuntimeError(_openai_transient_error_message(url, last_exc)) from last_exc

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
        last_exc: Exception | None = None
        for attempt in range(_OPENAI_MAX_RETRIES):
            try:
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
                            return
                        try:
                            obj = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        choices = obj.get("choices") or []
                        if not choices:
                            continue
                        choice0 = choices[0]
                        delta = choice0.get("delta") or {}
                        raw_chunk = delta.get("content")
                        # Claude API 代理有时返回数组 content，提取文本
                        chunk = _extract_text_from_content(raw_chunk) if raw_chunk is not None else ""
                        if chunk:
                            yield chunk
                        if choice0.get("finish_reason") or obj.get("done"):
                            return
                return
            except httpx.ReadTimeout as e:
                raise RuntimeError(_openai_timeout_message(url, e)) from e
            except _OPENAI_RETRYABLE as e:
                last_exc = e
                if attempt < _OPENAI_MAX_RETRIES - 1:
                    await asyncio.sleep(_OPENAI_RETRY_DELAYS[attempt])
        raise RuntimeError(_openai_transient_error_message(url, last_exc)) from last_exc

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
