"""
Pluggable LLM transport: not tied to Ollama.

- ollama: native /api/chat (default, unchanged behavior).
- openai_compatible: POST {OPENAI_BASE_URL}/chat/completions — works with
  vLLM, LiteLLM, LocalAI, your own FastAPI shim, etc., as long as it follows
  the OpenAI chat schema.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from agent_runtime import get_runtime


def _ollama_connection_message(url: str, exc: Exception) -> str:
    return (
        f"无法连接 Ollama（{url}）：{exc}。"
        "请先启动 Ollama：托盘图标、运行 ollama serve，或重新打开 ONYX-OVERRIDE（会自动尝试启动）。"
        "安装：https://ollama.com"
    )


def _ollama_bad_route_message(url: str, status_code: int, error_text: str = "") -> str:
    """Explain whether a 404 came from a bad Ollama route or an unavailable model."""
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
    """Ollama can spend a long time loading a large local model before returning the first byte."""
    c = min(60.0, max(10.0, float(total_sec)))
    return httpx.Timeout(connect=c, read=None, write=c, pool=5.0)


def _streaming_http_timeout(total_sec: float) -> httpx.Timeout:
    c = min(60.0, max(10.0, float(total_sec)))
    return httpx.Timeout(connect=c, read=None, write=c, pool=5.0)


def _ollama_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return messages


def _ollama_chat_options(temperature: float) -> dict[str, Any]:
    """Ollama /api/chat options; num_ctx only sent when OLLAMA_NUM_CTX>0."""
    rt = get_runtime()
    opts: dict[str, Any] = {"temperature": temperature}
    if rt.ollama_num_ctx > 0:
        opts["num_ctx"] = int(rt.ollama_num_ctx)
    return opts


def _openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"role": m["role"], "content": m.get("content", "")} for m in messages if m.get("content") is not None]


def _openai_chat_url_headers_body(
    rt: Any, messages: list[dict[str, Any]], model: str, *, temperature: float, stream: bool
) -> tuple[str, dict[str, str], dict[str, Any]]:
    base = rt.openai_base_url.rstrip("/")
    if not base:
        raise RuntimeError(
            "LLM_BACKEND=openai_compatible 但未设置 OPENAI_BASE_URL（例如 http://127.0.0.1:8000/v1）"
        )
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


def chat_complete_sync(
    messages: list[dict[str, Any]],
    model: str,
    *,
    temperature: float = 0.1,
    http_timeout_sec: float | None = None,
) -> str:
    rt = get_runtime()
    timeout = float(rt.ollama_timeout_sec)
    if http_timeout_sec is not None:
        timeout = min(timeout, max(5.0, float(http_timeout_sec)))
    if rt.llm_backend == "openai_compatible":
        url, headers, body = _openai_chat_url_headers_body(
            rt, messages, model, temperature=temperature, stream=False
        )
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        return _openai_non_stream_content(data)

    url = rt.ollama_chat_url()
    try:
        with httpx.Client(timeout=_ollama_request_timeout(float(timeout))) as client:
            resp = client.post(
                url,
                json={
                    "model": model,
                    "messages": _ollama_messages(messages),
                    "stream": False,
                    "options": _ollama_chat_options(temperature),
                },
            )
            error_text = resp.text
            if resp.status_code == 404:
                raise RuntimeError(_ollama_bad_route_message(url, 404, error_text))
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError as e:
        raise RuntimeError(_ollama_connection_message(rt.ollama_base, e)) from e
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
        url, headers, body = _openai_chat_url_headers_body(
            rt, messages, model, temperature=temperature, stream=False
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        return _openai_non_stream_content(data)

    url = rt.ollama_chat_url()
    try:
        async with httpx.AsyncClient(timeout=_ollama_request_timeout(float(timeout))) as client:
            resp = await client.post(
                url,
                json={
                    "model": model,
                    "messages": _ollama_messages(messages),
                    "stream": False,
                    "options": _ollama_chat_options(temperature),
                },
            )
            error_text = resp.text
            if resp.status_code == 404:
                raise RuntimeError(_ollama_bad_route_message(url, 404, error_text))
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError as e:
        raise RuntimeError(_ollama_connection_message(rt.ollama_base, e)) from e
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
        url, headers, body = _openai_chat_url_headers_body(
            rt, messages, model, temperature=temperature, stream=True
        )
        async with httpx.AsyncClient(timeout=_streaming_http_timeout(float(timeout))) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
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
                    # 任一结束信号都退出，避免等到连接超时
                    if choice0.get("finish_reason") or obj.get("done"):
                        break
        return

    url = rt.ollama_chat_url()
    try:
        async with httpx.AsyncClient(timeout=_streaming_http_timeout(float(timeout))) as client:
            async with client.stream(
                "POST",
                url,
                json={
                    "model": model,
                    "messages": _ollama_messages(messages),
                    "stream": True,
                    "options": _ollama_chat_options(temperature),
                },
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
