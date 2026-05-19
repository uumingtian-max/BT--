"""Capability executor for BKLT Blacklight.

Intent routing decides what the user likely wants. The runtime executes broad,
reversible capabilities with existing tools and returns concrete observations.
"""

from __future__ import annotations

from typing import Any, TypedDict

from capability_registry import get_capability
from capability_runtime import execute_runtime_capability
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


def execute_capability_request(
    message: str,
    *,
    capability_id: str | None = None,
    dry_run: bool = False,
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

    if dry_run:
        return _preview(cap, route, plan, dry_run=True, summary="已生成能力执行预案，未执行真实动作。")

    runtime = execute_runtime_capability(selected_id, message)
    return {
        "ok": bool(runtime.get("ok")),
        "dry_run": False,
        "executed": bool(runtime.get("observations")),
        "capability_id": selected_id,
        "risk_level": cap["risk_level"],
        "requires_confirmation": bool(cap.get("requires_confirmation")),
        "summary": runtime.get("summary") or f"已处理能力：{cap['title']}",
        "plan": plan,
        "observations": runtime.get("observations", []),
        "result": {"route": route, "capability": cap, "runtime": runtime},
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
