"""HTTP 请求工具（Agent 可调用，与前端工具面板一致）。"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlparse

import httpx

MAX_RESPONSE_BYTES = int(os.environ.get("AGENT_HTTP_MAX_RESPONSE_BYTES", str(2 * 1024 * 1024)))
ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


def _valid_http_url(url: str) -> bool:
    parsed = urlparse(url or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _read_limited_text(resp: httpx.Response) -> str:
    content_length = resp.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_RESPONSE_BYTES:
        return f"http_request error: response too large ({content_length} bytes > {MAX_RESPONSE_BYTES})"
    data = bytearray()
    for chunk in resp.iter_bytes():
        if not chunk:
            continue
        data.extend(chunk)
        if len(data) > MAX_RESPONSE_BYTES:
            return f"http_request error: response exceeded {MAX_RESPONSE_BYTES} bytes"
    return bytes(data).decode(resp.encoding or "utf-8", errors="replace")


def http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, Any] | None = None,
    body: str | dict[str, Any] | None = None,
    timeout_sec: float = 30.0,
) -> str:
    url = (url or "").strip()
    if not _valid_http_url(url):
        return "http_request error: url 必须以 http:// 或 https:// 开头"
    method = (method or "GET").upper()
    if method not in ALLOWED_METHODS:
        return f"http_request error: unsupported method {method}"
    hdrs = dict(headers or {})
    try:
        timeout = min(120.0, max(5.0, float(timeout_sec)))
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            kwargs: dict[str, Any] = {"headers": hdrs}
            if body is not None and method not in ("GET", "HEAD"):
                if isinstance(body, dict):
                    kwargs["json"] = body
                else:
                    kwargs["content"] = str(body)
            with client.stream(method, url, **kwargs) as resp:
                ctype = (resp.headers.get("content-type") or "").lower()
                text = _read_limited_text(resp)
        ctype = (resp.headers.get("content-type") or "").lower()
        if text.startswith("http_request error:"):
            return text
        if "application/json" in ctype and text:
            try:
                text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
            except Exception:
                pass
        if len(text) > 12000:
            text = text[:12000] + "\n…(truncated)"
        return f"HTTP {resp.status_code}\n{text}"
    except Exception as e:
        return f"http_request error: {e}"
