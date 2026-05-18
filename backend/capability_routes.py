"""HTTP routes for the BKLT capability control plane."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from capability_registry import get_capability, list_capabilities, validate_capabilities
from intent_router import route_intent
from tool_registry import all_tool_names

router = APIRouter()


class IntentRouteRequest(BaseModel):
    message: str = Field(..., min_length=1)
    max_matches: int = Field(default=4, ge=1, le=8)


@router.get("/capabilities")
def capabilities():
    """List user-facing capabilities above the low-level tool registry."""
    return {"ok": True, "items": list_capabilities()}


@router.get("/capabilities/health")
def capabilities_health():
    problems = validate_capabilities(set(all_tool_names()))
    return {"ok": not problems, "problems": problems, "count": len(list_capabilities())}


@router.get("/capabilities/{capability_id}")
def capability_detail(capability_id: str):
    try:
        return {"ok": True, "item": get_capability(capability_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/intent/route")
def intent_route(body: IntentRouteRequest):
    """Route natural language into candidate capabilities without executing tools."""
    return {"ok": True, "route": route_intent(body.message, max_matches=body.max_matches)}
