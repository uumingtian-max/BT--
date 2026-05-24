from fastapi import APIRouter

from agent_events import timeline_contract
from tool_registry import TOOL_GROUPS, get_full_registry, list_tool_metadata, validate_tool_registry

router = APIRouter()


@router.get("/tools/full")
def full_tool_registry():
    """兼容别名：返回 get_full_registry()。新代码请用 GET /meta/tools/registry。"""
    problems = validate_tool_registry()
    return {"ok": not problems, "data": get_full_registry(), "problems": problems}


@router.get("/tools/registry")
def tool_registry_status():
    """UI-ready Agent tool registry.

    This endpoint is designed for the desktop workbench: the frontend can render
    tool cards, risk badges, parameter forms, and future confirmation dialogs
    without importing backend internals.
    """
    problems = validate_tool_registry()
    tools = list_tool_metadata()
    return {
        "ok": not problems,
        "count": len(tools),
        "groups": TOOL_GROUPS,
        "tools": tools,
        "problems": problems,
    }


@router.get("/tools/risks")
def tool_risk_summary():
    """Compact risk summary for safety gates and UI badges."""
    buckets = {"safe": [], "confirm": [], "dangerous": []}
    for item in list_tool_metadata():
        buckets[item["risk_level"]].append(item["name"])
    return {
        "ok": True,
        "risk_levels": buckets,
        "counts": {key: len(value) for key, value in buckets.items()},
    }


@router.get("/agent/timeline/contract")
def agent_timeline_contract():
    """Frontend contract for rendering Agent run timelines."""
    return {"ok": True, **timeline_contract()}
