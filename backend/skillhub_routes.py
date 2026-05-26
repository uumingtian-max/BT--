"""API routes for BKLT SkillHub."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from skillhub import audit_skillhub, get_skillhub_record, list_skillhub_records, skillhub_summary
from skill_evolution import (
    approve_skill_candidate,
    list_skill_candidates,
    propose_skill_candidate,
    reject_skill_candidate,
)

router = APIRouter()


@router.get("/skillhub/summary")
def skillhub_summary_route():
    return skillhub_summary()


@router.get("/skillhub/registry")
def skillhub_registry(include_content: bool = False, source: str | None = None, risk_level: str | None = None):
    records = list_skillhub_records()
    if source:
        records = [item for item in records if item.source == source]
    if risk_level:
        records = [item for item in records if item.risk_level == risk_level]
    return {
        "ok": True,
        "count": len(records),
        "skills": [item.to_dict(include_content=include_content) for item in records],
    }


@router.get("/skillhub/audit")
def skillhub_audit_route():
    return audit_skillhub()


@router.get("/skillhub/skills/{skill_id}")
def skillhub_skill_detail(skill_id: str):
    record = get_skillhub_record(skill_id)
    if not record:
        raise HTTPException(404, "skill not found")
    return {"ok": True, "skill": record.to_dict(include_content=True)}


@router.get("/skillhub/candidates")
def skillhub_candidates(status: str | None = None):
    return {"ok": True, "candidates": list_skill_candidates(status=status)}


@router.post("/skillhub/candidates")
def skillhub_candidate_propose(payload: dict):
    try:
        return propose_skill_candidate(
            summary=str(payload.get("summary") or ""),
            evidence=[str(x) for x in (payload.get("evidence") or [])],
            trigger_hints=[str(x) for x in (payload.get("trigger_hints") or [])],
            title=str(payload.get("title") or "") or None,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/skillhub/candidates/{candidate_id}/approve")
def skillhub_candidate_approve(candidate_id: str):
    try:
        return approve_skill_candidate(candidate_id)
    except KeyError as exc:
        raise HTTPException(404, "candidate not found") from exc


@router.post("/skillhub/candidates/{candidate_id}/reject")
def skillhub_candidate_reject(candidate_id: str, payload: dict | None = None):
    try:
        return reject_skill_candidate(candidate_id, reason=str((payload or {}).get("reason") or ""))
    except KeyError as exc:
        raise HTTPException(404, "candidate not found") from exc
