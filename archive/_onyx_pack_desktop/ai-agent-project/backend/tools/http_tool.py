"""HTTP 请求工具（Agent 可调用，与前端工具面板一致）。"""

from __future__ import annotations

import json
from typing import Any

import httpx


def http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, Any] | None = None,
    body: str | dict[str, Any] | None = None,
    timeout_sec: float = 30.0,
) -> str:
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return "http_request error: url 必须以 http:// 或 https:// 开头"
    method = (method or "GET").upper()
    hdrs = dict(headers or {})
    try:
        with httpx.Client(timeout=min(120.0, max(5.0, float(timeout_sec))), follow_redirects=True) as client:
            kwargs: dict[str, Any] = {"headers": hdrs}
            if body is not None and method not in ("GET", "HEAD"):
                if isinstance(body, dict):
                    kwargs["json"] = body
                else:
                    kwargs["content"] = str(body)
            resp = client.request(method, url, **kwargs)
        ctype = (resp.headers.get("content-type") or "").lower()
        text = resp.text
        if "application/json" in ctype:
            try:
                text = json.dumps(resp.json(), ensure_ascii=False, indent=2)
            except Exception:
                pass
        if len(text) > 12000:
            text = text[:12000] + "\n…(truncated)"
        return f"HTTP {resp.status_code}\n{text}"
    except Exception as e:
        return f"http_request error: {e}"
