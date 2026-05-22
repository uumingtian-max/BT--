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
    try:
        from run_graph_store import append_visual_event

        append_visual_event(
            event_id=event["id"],
            event_type=event_type,
            source=source,
            title=title,
            status=status,
            payload=payload or {},
            run_id=run_id,
            created_at=event["created_at"],
        )
    except Exception:
        pass
    return event


def list_events(*, limit: int = 100, source: str | None = None, run_id: str | None = None) -> list[dict[str, Any]]:
    """Return recent events newest-first (SQLite + in-memory merge)."""
    limit = max(1, min(500, int(limit or 100)))
    persisted: list[dict[str, Any]] = []
    try:
        from run_graph_store import list_visual_events

        persisted = list_visual_events(limit=limit, source=source, run_id=run_id)
    except Exception:
        persisted = []
    with _LOCK:
        memory = list(_EVENTS)
    if source:
        memory = [item for item in memory if item.get("source") == source]
    if run_id:
        memory = [item for item in memory if item.get("run_id") == run_id]
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for item in persisted + memory:
        eid = str(item.get("id") or "")
        if eid and eid in seen:
            continue
        if eid:
            seen.add(eid)
        merged.append(item)
        if len(merged) >= limit:
            break
    return merged[:limit]


def clear_events() -> None:
    """Clear the in-memory event buffer. Intended for tests and local debugging."""
    with _LOCK:
        _EVENTS.clear()
    try:
        import os

        from run_graph_store import DB_PATH, init_run_graph_db

        init_run_graph_db()
        if os.environ.get("RUN_GRAPH_TEST_CLEAR") == "1" and os.path.isfile(DB_PATH):
            import sqlite_wal as sqlite3

            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("DELETE FROM visual_events")
                conn.commit()
    except Exception:
        pass
