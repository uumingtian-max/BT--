"""Optional HTTP access log (REQUEST_LOG=1)."""

from __future__ import annotations

import logging
import os
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_log = logging.getLogger("ai_agent.request")


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - t0) * 1000.0
        _log.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            ms,
        )
        return response


def request_log_enabled() -> bool:
    return os.environ.get("REQUEST_LOG", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
