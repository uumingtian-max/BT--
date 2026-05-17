"""REST API for local automation workbench."""

from __future__ import annotations

import json
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from automation_runner import automation_capabilities, normalize_target, normalize_task_kind, run_automation_task
from automation_store import create_job, delete_job, get_job, list_jobs, list_runs, set_job_enabled
from visual_event_bus import list_events

router = APIRouter()


class AutomationRunRequest(BaseModel):
    task_kind: str = "project_check"
    target: str = "all"


class AutomationJobCreate(BaseModel):
    name: str = "自动化任务"
    task_kind: str = "project_check"
    target: str = "all"
    enabled: bool = True
    params: dict = Field(default_factory=dict)


@router.get("/capabilities")
def capabilities():
    return {"ok": True, "capabilities": automation_capabilities()}


@router.get("/jobs")
def jobs_list():
    return {"ok": True, "jobs": list_jobs()}


@router.post("/jobs")
def jobs_create(body: AutomationJobCreate):
    try:
        task_kind = normalize_task_kind(body.task_kind)
        target = normalize_target(body.target)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    job = create_job(
        name=body.name,
        task_kind=task_kind,
        target=target,
        params_json=json.dumps(body.params or {}, ensure_ascii=False),
        enabled=body.enabled,
    )
    return {"ok": True, "job": job}


@router.delete("/jobs/{job_id}")
def jobs_delete(job_id: str):
    if not delete_job(job_id):
        raise HTTPException(404, "automation job not found")
    return {"ok": True}


@router.post("/jobs/{job_id}/enable")
def jobs_enable(job_id: str, enabled: bool = True):
    if not set_job_enabled(job_id, enabled):
        raise HTTPException(404, "automation job not found")
    return {"ok": True, "enabled": enabled}


@router.post("/jobs/{job_id}/run")
def jobs_run(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "automation job not found")
    try:
        result = run_automation_task(task_kind=job["task_kind"], target=job["target"], job_id=job_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": result.get("status") == "success", "run": result}


@router.post("/run")
def run_once(body: AutomationRunRequest):
    try:
        result = run_automation_task(task_kind=body.task_kind, target=body.target)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": result.get("status") == "success", "run": result}


@router.get("/runs")
def runs_list(limit: int = 50):
    return {"ok": True, "runs": list_runs(limit=limit)}


@router.get("/events")
def events_list(limit: int = 100, run_id: str | None = None):
    return {"ok": True, "events": list_events(limit=limit, source="automation", run_id=run_id)}
