"""HTTP routes for the BKLT capability control plane."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from capability_executor import execute_capability_request
from capability_registry import get_capability, list_capabilities, validate_capabilities
from intent_router import route_intent
from tool_registry import all_tool_names

router = APIRouter()


class IntentRouteRequest(BaseModel):
    message: str = Field(..., min_length=1)
    max_matches: int = Field(default=4, ge=1, le=8)


class CapabilityExecuteRequest(BaseModel):
    message: str = Field(..., min_length=1)
    capability_id: str | None = None
    dry_run: bool = True
    allow_confirmed: bool = False


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


@router.post("/capabilities/execute")
def capability_execute(body: CapabilityExecuteRequest):
    """Preview or safely execute a capability request.

    V1 only executes safe/read-only handlers. Risky capabilities return a plan.
    """
    return {
        "ok": True,
        "execution": execute_capability_request(
            body.message,
            capability_id=body.capability_id,
            dry_run=body.dry_run,
            allow_confirmed=body.allow_confirmed,
        ),
    }
