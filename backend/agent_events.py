"""Agent run event helpers for the desktop workbench timeline.

The existing `/agent/run` endpoint already streams coarse steps such as
`thinking`, `tool_call`, `tool_result`, and `final_answer`.  This module turns
those loose dictionaries into a stable UI-facing event shape.  Keeping the
normalizer separate lets the frontend, tests, and future persistence layer share
one contract without coupling to the full Agent runtime.
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
    "final_answer",
    "error",
    "done",
]

AgentEventStatus = Literal["pending", "running", "success", "failed", "skipped"]


TIMELINE_EVENT_TYPES: list[dict[str, str]] = [
    {"type": "user_goal", "label": "用户目标", "description": "用户提交给 Agent 的原始任务。"},
    {"type": "thinking", "label": "思考 / 计划", "description": "Agent 的阶段性计划、判断或执行意图。"},
    {"type": "tool_call", "label": "工具调用", "description": "Agent 选择并准备执行的工具。"},
    {"type": "tool_result", "label": "工具结果", "description": "工具执行返回的真实结果、摘要或错误。"},
    {"type": "final_answer", "label": "最终回答", "description": "基于真实执行结果生成的最终回复。"},
    {"type": "error", "label": "错误", "description": "运行时异常或工具失败的标准化描述。"},
    {"type": "done", "label": "完成", "description": "一次 Agent run 的结束标记。"},
]


EVENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["run_id", "step_id", "index", "type", "status", "created_at"],
    "properties": {
        "run_id": {"type": "string"},
        "step_id": {"type": "string"},
        "index": {"type": "integer", "minimum": 0},
        "type": {"enum": [item["type"] for item in TIMELINE_EVENT_TYPES]},
        "status": {"enum": ["pending", "running", "success", "failed", "skipped"]},
        "title": {"type": "string"},
        "content": {"type": "string"},
        "tool": {"type": ["string", "null"]},
        "risk_level": {"enum": ["safe", "confirm", "dangerous", None]},
        "params": {"type": ["object", "null"]},
        "result": {"type": ["string", "object", "array", "number", "boolean", "null"]},
        "error": {"type": ["string", "null"]},
        "created_at": {"type": "string", "format": "date-time"},
    },
}


def new_run_id() -> str:
    return str(uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _status_for_step(step: dict[str, Any]) -> AgentEventStatus:
    if step.get("status") in {"pending", "running", "success", "failed", "skipped"}:
        return step["status"]
    text = " ".join(str(step.get(key, "")) for key in ("content", "result", "error")).lower()
    if step.get("error") or "tool error:" in text or " error:" in text or "failed" in text or "失败" in text:
        return "failed"
    if step.get("type") == "tool_call":
        return "running"
    return "success"


def _title_for_step(event_type: str, tool_name: str | None) -> str:
    if event_type == "tool_call" and tool_name:
        return f"调用工具：{tool_name}"
    if event_type == "tool_result" and tool_name:
        return f"工具结果：{tool_name}"
    titles = {
        "user_goal": "用户目标",
        "thinking": "思考 / 计划",
        "tool_call": "工具调用",
        "tool_result": "工具结果",
        "final_answer": "最终回答",
        "error": "错误",
        "done": "完成",
    }
    return titles.get(event_type, event_type)


def _risk_for_tool(tool_name: str | None) -> str | None:
    if not tool_name:
        return None
    try:
        return get_tool_metadata(tool_name)["risk_level"]
    except KeyError:
        return None


def normalize_agent_step(step: dict[str, Any], *, run_id: str, index: int) -> dict[str, Any]:
    """Normalize one loose Agent step into a timeline event.

    The function is deliberately permissive: unknown step fields are preserved in
    `raw`, while common fields are copied into predictable top-level keys.
    """
    event_type = str(step.get("type") or "thinking")
    if event_type not in {item["type"] for item in TIMELINE_EVENT_TYPES}:
        event_type = "thinking"
    tool_name = step.get("tool") if isinstance(step.get("tool"), str) else None
    content = step.get("content")
    result = step.get("result")
    error = step.get("error")
    return {
        "run_id": run_id,
        "step_id": str(step.get("step_id") or uuid4()),
        "index": index,
        "type": event_type,
        "status": _status_for_step(step),
        "title": str(step.get("title") or _title_for_step(event_type, tool_name)),
        "content": "" if content is None else str(content),
        "tool": tool_name,
        "risk_level": _risk_for_tool(tool_name),
        "params": step.get("params") if isinstance(step.get("params"), dict) else None,
        "result": result,
        "error": None if error is None else str(error),
        "created_at": str(step.get("created_at") or _now_iso()),
        "raw": dict(step),
    }


def normalize_agent_steps(steps: list[dict[str, Any]], *, run_id: str | None = None) -> list[dict[str, Any]]:
    rid = run_id or new_run_id()
    return [normalize_agent_step(step, run_id=rid, index=index) for index, step in enumerate(steps)]


def timeline_contract() -> dict[str, Any]:
    """Return the frontend-facing timeline contract."""
    return {
        "event_types": TIMELINE_EVENT_TYPES,
        "schema": EVENT_SCHEMA,
        "status_values": ["pending", "running", "success", "failed", "skipped"],
        "risk_values": ["safe", "confirm", "dangerous"],
    }
