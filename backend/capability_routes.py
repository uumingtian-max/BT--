"""HTTP routes for the BKLT capability control plane."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from capability_executor import execute_capability_request
from capability_registry import get_capability, list_capabilities, validate_capabilities
from intent_router import route_intent
from specialist_registry import (
    get_specialist,
    list_specialists,
    route_specialists,
    validate_specialists,
)
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
    capability_problems = validate_capabilities(set(all_tool_names()))
    capability_ids = {item["id"] for item in list_capabilities()}
    specialist_problems = validate_specialists(capability_ids)
    problems = capability_problems + specialist_problems
    return {
        "ok": not problems,
        "problems": problems,
        "count": len(list_capabilities()),
        "specialist_count": len(list_specialists()),
    }


@router.get("/capabilities/{capability_id}")
def capability_detail(capability_id: str):
    try:
        return {"ok": True, "item": get_capability(capability_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/intent/route")
def intent_route(body: IntentRouteRequest):
    """Route natural language into capabilities and specialist roles without executing tools."""
    return {
        "ok": True,
        "route": route_intent(body.message, max_matches=body.max_matches),
        "specialists": route_specialists(body.message, max_matches=min(body.max_matches, 5)),
    }


@router.get("/specialists")
def specialists():
    """List routing specialists used by the orchestrator/control plane."""
    return {"ok": True, "items": list_specialists()}


@router.get("/specialists/{specialist_id}")
def specialist_detail(specialist_id: str):
    try:
        return {"ok": True, "item": get_specialist(specialist_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/specialists/route")
def specialist_route(body: IntentRouteRequest):
    """Route natural language into specialist lenses without executing tools."""
    return {"ok": True, "matches": route_specialists(body.message, max_matches=body.max_matches)}


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


@router.get("/evolution-cockpit")
def evolution_cockpit():
    """Single payload for the frontend evolution cockpit.

    This endpoint intentionally composes existing local subsystems instead of
    starting work by itself. The UI can poll it cheaply to render the current
    state of SkillHub, automation, specialists, capabilities, and visual events.
    """
    payload: dict[str, object] = {
        "ok": True,
        "capabilities": {"count": len(list_capabilities()), "items": list_capabilities()},
        "specialists": {"count": len(list_specialists()), "items": list_specialists()},
    }

    try:
        from skillhub import audit_skillhub, skillhub_summary

        payload["skillhub"] = {"summary": skillhub_summary(), "audit": audit_skillhub()}
    except Exception as exc:  # pragma: no cover - defensive dashboard fallback
        payload["skillhub"] = {"ok": False, "error": str(exc)}

    try:
        from automation_store import list_jobs, list_runs

        jobs = list_jobs()
        runs = list_runs(limit=10)
        payload["automation"] = {"jobs_count": len(jobs), "runs_count": len(runs), "jobs": jobs, "recent_runs": runs}
    except Exception as exc:  # pragma: no cover - defensive dashboard fallback
        payload["automation"] = {"ok": False, "error": str(exc)}

    try:
        from visual_event_bus import list_events

        payload["events"] = {"count": len(list_events(limit=50)), "items": list_events(limit=50)}
    except Exception as exc:  # pragma: no cover - defensive dashboard fallback
        payload["events"] = {"ok": False, "error": str(exc)}

    try:
        from habit_pipeline import get_habit_status

        payload["habit"] = get_habit_status()
    except Exception as exc:  # pragma: no cover - defensive dashboard fallback
        payload["habit"] = {"ok": False, "error": str(exc)}

    return payload
