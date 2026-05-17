"""Agent run event schema helpers.

The existing `/agent/run` endpoint already streams coarse step dictionaries such
as `thinking`, `tool_call`, `tool_result`, and `final_answer`.  This module adds
an explicit event shape that the frontend can render as a timeline and that the
backend can later persist for replay, analytics, and debugging.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from tool_registry import get_tool_metadata

AgentEventType = Literal[
    "user_goal",
    "thinking",
    "tool_call",
    "tool_result",
    "context_compression",
    "final_answer",
    "memory_write",
    "error",
]

AgentEventStatus = Literal["pending", "running", "success", "failed", "skipped"]


def utc_now_iso() -> str:
    """Return an ISO timestamp with a stable UTC suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_run_id() -> str:
    return str(uuid4())


def new_step_id() -> str:
    return str(uuid4())


def event_from_legacy_step(
    step: dict[str, Any],
    *,
    run_id: str,
    index: int,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Convert an existing Agent step dictionary into a UI-ready event.

    The function keeps the legacy fields so older frontends keep working, while
    adding stable ids, timestamps, status, risk information, and display labels.
    """
    event_type = str(step.get("type") or "thinking")
    ts = timestamp or utc_now_iso()
    tool = step.get("tool")
    risk_level = None
    display_name = None
    group = None
    input_schema = None

    if tool:
        try:
            meta = get_tool_metadata(str(tool))
            risk_level = meta["risk_level"]
            display_name = meta["description"]
            group = meta["group"]
            input_schema = meta["input_schema"]
        except KeyError:
            risk_level = "confirm"
            display_name = str(tool)

    status: AgentEventStatus = "success"
    if event_type == "tool_call":
        status = "running"
    elif event_type == "error":
        status = "failed"
    elif event_type == "tool_result" and _looks_like_error(step.get("result")):
        status = "failed"

    event: dict[str, Any] = dict(step)
    event.update(
        {
            "run_id": run_id,
            "step_id": str(step.get("step_id") or new_step_id()),
            "index": index,
            "event_type": event_type,
            "status": status,
            "risk_level": risk_level,
            "tool_group": group,
            "tool_display_name": display_name,
            "tool_input_schema": input_schema,
            "started_at": step.get("started_at") or ts,
            "ended_at": step.get("ended_at") or (None if status == "running" else ts),
            "duration_ms": step.get("duration_ms"),
            "error": step.get("error"),
        }
    )
    return event


def enrich_legacy_steps(steps: list[dict[str, Any]], *, run_id: str | None = None) -> list[dict[str, Any]]:
    """Return UI-ready timeline events for a list of legacy Agent steps."""
    rid = run_id or new_run_id()
    return [event_from_legacy_step(step, run_id=rid, index=i) for i, step in enumerate(steps)]


def summarize_timeline(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compact metrics for one Agent run timeline."""
    tools = [e.get("tool") for e in events if e.get("tool")]
    failed = [e for e in events if e.get("status") == "failed"]
    risk_counts = {"safe": 0, "confirm": 0, "dangerous": 0, "unknown": 0}
    for event in events:
        risk = event.get("risk_level") or "unknown"
        if risk not in risk_counts:
            risk = "unknown"
        risk_counts[risk] += 1
    return {
        "run_id": events[0].get("run_id") if events else None,
        "step_count": len(events),
        "tool_call_count": sum(1 for e in events if e.get("event_type") == "tool_call"),
        "unique_tools": sorted({str(t) for t in tools if t}),
        "failed_step_count": len(failed),
        "risk_counts": risk_counts,
        "has_final_answer": any(e.get("event_type") == "final_answer" for e in events),
    }


def _looks_like_error(value: Any) -> bool:
    text = str(value or "").lower()
    return any(marker in text for marker in ("error:", "tool error", "traceback", "timeout", "failed"))
