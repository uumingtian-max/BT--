"""Tool execution policy: risk gates + dispatch (registry is source of truth for risk)."""

from __future__ import annotations

import os
from typing import Any, Callable

from tool_registry import RiskLevel, get_tool_metadata

ToolHandler = Callable[[dict[str, Any]], str]


def tool_auto_confirm_enabled() -> bool:
    """When true, confirm/dangerous tools run without explicit confirmed=true."""
    return os.environ.get("AGENT_TOOL_AUTO_CONFIRM", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def get_tool_risk_level(tool_name: str) -> RiskLevel | None:
    try:
        return get_tool_metadata(tool_name)["risk_level"]
    except KeyError:
        return None


def tool_requires_confirmation(tool_name: str, params: dict[str, Any] | None = None) -> bool:
    if tool_auto_confirm_enabled():
        return False
    risk = get_tool_risk_level(tool_name)
    if risk not in ("confirm", "dangerous"):
        return False
    p = params or {}
    return not (p.get("confirmed") is True or p.get("_user_confirmed") is True)


def check_tool_execution(
    tool_name: str,
    params: dict[str, Any] | None = None,
    *,
    tool_map: dict[str, ToolHandler] | None = None,
) -> dict[str, Any] | None:
    """
    Return None if execution may proceed.
    Otherwise return a structured block dict for the agent loop (confirm_required / error).
    """
    params = params or {}
    if tool_map is not None and tool_name not in tool_map:
        return {
            "status": "error",
            "message": f"Unknown tool: {tool_name}",
        }
    try:
        get_tool_metadata(tool_name)
    except KeyError:
        if tool_map is not None and tool_name in tool_map:
            return None
        return {
            "status": "error",
            "message": f"Unknown tool: {tool_name}",
        }

    if tool_requires_confirmation(tool_name, params):
        risk = get_tool_risk_level(tool_name) or "confirm"
        return {
            "status": "confirm_required",
            "tool": tool_name,
            "risk_level": risk,
            "message": (
                f"工具 `{tool_name}` 为 {risk} 级别，需用户确认后再执行。"
                "请在 parameters 中加入 \"confirmed\": true 后重试，"
                "或设置环境变量 AGENT_TOOL_AUTO_CONFIRM=1（仅建议本机开发）。"
            ),
        }
    return None


_ORCHESTRATION_MARKERS = (
    "编排",
    "用编排",
    "多模型",
    "多角色",
    "协作审查",
    "协作汇总",
    "任务分解",
    "复杂方案",
    "方案对比",
    "对比方案",
    "复杂任务",
    "orchestrate",
    "orchestration",
)


def _search_params_look_like_orchestration(params: dict[str, Any]) -> bool:
    query = str(
        params.get("query")
        or params.get("q")
        or params.get("search")
        or params.get("text")
        or ""
    ).lower()
    return bool(query) and any(marker.lower() in query for marker in _ORCHESTRATION_MARKERS)


def _maybe_force_orchestration(tool_name: str, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Correct bad deterministic/LLM routing before execution.

    Requests such as “用编排做一个复杂方案对比” must invoke the orchestration
    tool.  If an earlier heuristic incorrectly picked search, redirect here.
    """
    if tool_name in {"local_search", "web_search"} and _search_params_look_like_orchestration(params):
        message = str(params.get("query") or params.get("q") or params.get("search") or params.get("text") or "").strip()
        return "run_task_orchestration", {"message": message}
    return tool_name, params


def execute_tool_sync(
    tool_name: str,
    params: dict[str, Any],
    tool_map: dict[str, ToolHandler],
) -> str:
    tool_name, params = _maybe_force_orchestration(tool_name, params or {})
    block = check_tool_execution(tool_name, params, tool_map=tool_map)
    if block:
        return block["message"]
    fn = tool_map.get(tool_name)
    if not fn:
        return f"Unknown tool: {tool_name}"
    return fn(params)