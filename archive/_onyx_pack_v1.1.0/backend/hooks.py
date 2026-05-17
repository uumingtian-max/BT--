"""Optional outbound webhooks after agent runs (integrate with n8n / your own bus)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from agent_runtime import get_runtime

_log = logging.getLogger("ai_agent.hooks")


async def notify_agent_completed(payload: dict[str, Any]) -> None:
    rt = get_runtime()
    url = (rt.webhook_url or "").strip()
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            await client.post(url, json=payload)
    except Exception as exc:
        _log.warning("webhook post failed: %s", exc)
