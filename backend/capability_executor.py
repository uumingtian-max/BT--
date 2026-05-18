"""Capability executor for BKLT Blacklight.

The intent router decides *what* a user likely wants.  This module is the next
layer: it turns a capability plan into a guarded execution preview or a limited
safe execution.

Version 1 deliberately executes only read-only/safe capabilities.  Confirm and
dangerous capabilities return a structured plan until the UI approval + rollback
flow exists.
"""

from __future__ import annotations

import json
from typing import Any, TypedDict

from capability_registry import get_capability
from intent_router import route_intent


class CapabilityExecution(TypedDict):
    ok: bool
    dry_run: bool
    executed: bool
    capability_id: str
    risk_level: str
    requires_confirmation: bool
    summary: str
    plan: list[dict[str, Any]]
    observations: list[dict[str, Any]]
    result: dict[str, Any]


SAFE_EXECUTION_HANDLERS = {
    "project.health_check": "run_project_check",
}


def execute_capability_request(
    message: str,
    *,
    capability_id: str | None = None,
    dry_run: bool = True,
    allow_confirmed: bool = False,
) -> CapabilityExecution:
    route = route_intent(message, max_matches=4)
    selected_id = capability_id or _first_capability_id(route)
    if not selected_id:
        return {
            "ok": False,
            "dry_run": dry_run,
            "executed": False,
            "capability_id": "unknown",
            "risk_level": "safe",
            "requires_confirmation": False,
            "summary": "没有匹配到可执行能力。",
            "plan": route.get("plan", []),
            "observations": [],
            "result": {"route": route},
        }

    cap = get_capability(selected_id)
    plan = _plan_for_capability(route, selected_id)
    risk = cap["risk_level"]
    needs_confirmation = bool(cap.get("requires_confirmation"))

    if dry_run:
        return _preview(cap, route, plan, dry_run=True, summary="已生成能力执行预案，未执行真实动作。")

    if risk != "safe" or needs_confirmation:
        return _preview(
            cap,
            route,
            plan,
            dry_run=False,
            summary="该能力需要确认或存在风险，当前只返回计划，不执行真实动作。",
        )

    handler_name = SAFE_EXECUTION_HANDLERS.get(selected_id)
    if not handler_name:
        return _preview(
            cap,
            route,
            plan,
            dry_run=False,
            summary="该安全能力暂未接入执行 handler，当前只返回计划。",
        )

    observations = []
    result_payload: dict[str, Any] = {"route": route}
    try:
        # Import lazily to avoid loading desktop/browser dependencies when merely
        # listing capabilities.
        from agent_tool_map import TOOL_MAP

        if handler_name == "run_project_check":
            raw = TOOL_MAP["run_project_check"]({"target": "all"})
            observations.append(
                {
                    "tool": "run_project_check",
                    "ok": "exit_code=0" in raw and "exit_code=1" not in raw,
                    "preview": raw[-4000:],
                }
            )
            result_payload["tool_output"] = raw
        return {
            "ok": True,
            "dry_run": False,
            "executed": True,
            "capability_id": selected_id,
            "risk_level": risk,
            "requires_confirmation": needs_confirmation,
            "summary": f"已执行安全能力：{cap['title']}",
            "plan": plan,
            "observations": observations,
            "result": result_payload,
        }
    except Exception as exc:
        return {
            "ok": False,
            "dry_run": False,
            "executed": False,
            "capability_id": selected_id,
            "risk_level": risk,
            "requires_confirmation": needs_confirmation,
            "summary": f"能力执行失败：{exc}",
            "plan": plan,
            "observations": observations,
            "result": result_payload,
        }


def _first_capability_id(route: dict[str, Any]) -> str | None:
    matches = route.get("matches") or []
    if not matches:
        return None
    cap = matches[0].get("capability") or {}
    return cap.get("id")


def _plan_for_capability(route: dict[str, Any], capability_id: str) -> list[dict[str, Any]]:
    plan = [step for step in (route.get("plan") or []) if step.get("capability_id") == capability_id]
    return plan or route.get("plan", [])


def _preview(
    cap: dict[str, Any],
    route: dict[str, Any],
    plan: list[dict[str, Any]],
    *,
    dry_run: bool,
    summary: str,
) -> CapabilityExecution:
    return {
        "ok": True,
        "dry_run": dry_run,
        "executed": False,
        "capability_id": cap["id"],
        "risk_level": cap["risk_level"],
        "requires_confirmation": bool(cap.get("requires_confirmation")),
        "summary": summary,
        "plan": plan,
        "observations": [],
        "result": {"route": route, "capability": cap},
    }
