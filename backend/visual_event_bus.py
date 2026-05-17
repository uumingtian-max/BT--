"""Lightweight in-process visual event bus.

The frontend workbench needs a simple way to inspect recent automation and Agent
execution events.  This module keeps a bounded in-memory event buffer that can be
exposed through REST today and later replaced or supplemented with SQLite/SSE.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

_MAX_EVENTS = 500
_EVENTS: deque[dict[str, Any]] = deque(maxlen=_MAX_EVENTS)
_LOCK = Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def publish_event(
    *,
    event_type: str,
    source: str,
    title: str,
    payload: dict[str, Any] | None = None,
    run_id: str | None = None,
    status: str = "info",
) -> dict[str, Any]:
    """Append an event and return the stored record."""
    event = {
        "id": str(uuid4()),
        "run_id": run_id,
        "type": event_type,
        "source": source,
        "title": title,
        "status": status,
        "payload": payload or {},
        "created_at": _now_iso(),
    }
    with _LOCK:
        _EVENTS.appendleft(event)
    return event


def list_events(*, limit: int = 100, source: str | None = None, run_id: str | None = None) -> list[dict[str, Any]]:
    """Return recent events newest-first."""
    limit = max(1, min(500, int(limit or 100)))
    with _LOCK:
        items = list(_EVENTS)
    if source:
        items = [item for item in items if item.get("source") == source]
    if run_id:
        items = [item for item in items if item.get("run_id") == run_id]
    return items[:limit]


def clear_events() -> None:
    """Clear the in-memory event buffer. Intended for tests and local debugging."""
    with _LOCK:
        _EVENTS.clear()
