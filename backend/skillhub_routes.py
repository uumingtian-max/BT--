"""API routes for BKLT SkillHub."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from skillhub import audit_skillhub, get_skillhub_record, list_skillhub_records, skillhub_summary

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
