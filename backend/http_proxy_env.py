"""出站 HTTP(S) 代理（inferaichat 等有 IP 白名单时用固定出口 VPS）。"""

from __future__ import annotations

import os


def httpx_proxy_url() -> str | None:
    for key in (
        "BKLT_HTTP_PROXY",
        "BKLT_API_HTTP_PROXY",
        "HTTPS_PROXY",
        "HTTP_PROXY",
    ):
        raw = (os.environ.get(key) or "").strip()
        if raw:
            return raw
    return None
