"""REST API for scheduled jobs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from scheduler_store import create_job, delete_job, get_job, list_jobs, set_job_enabled
from scheduler_runner import run_job_now

router = APIRouter()


class JobCreate(BaseModel):
    name: str = "定时任务"
    message: str
    interval_sec: int = Field(3600, ge=60, le=86400 * 7)
    task_kind: str = "agent"
    model: str | None = None
    delivery_webhook: str | None = None
    enabled: bool = True


@router.get("/jobs")
def jobs_list():
    return {"ok": True, "jobs": list_jobs()}


@router.post("/jobs")
def jobs_create(body: JobCreate):
    from model_lock import enforce_locked_model

    if body.task_kind not in ("agent", "chat", "habit_check"):
        raise HTTPException(400, "task_kind must be agent, chat, or habit_check")
    body.model = enforce_locked_model(body.model, user_input=body.message, mode=body.task_kind)
    job = create_job(
        name=body.name,
        message=body.message,
        interval_sec=body.interval_sec,
        task_kind=body.task_kind,
        model=body.model,
        delivery_webhook=body.delivery_webhook,
        enabled=body.enabled,
    )
    return {"ok": True, "job": job}


@router.delete("/jobs/{job_id}")
def jobs_delete(job_id: str):
    if not delete_job(job_id):
        raise HTTPException(404, "job not found")
    return {"ok": True}


@router.post("/jobs/{job_id}/enable")
def jobs_enable(job_id: str, enabled: bool = True):
    if not set_job_enabled(job_id, enabled):
        raise HTTPException(404, "job not found")
    return {"ok": True, "enabled": enabled}


@router.post("/jobs/{job_id}/run")
async def jobs_run_now(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    result = await run_job_now(job)
    return {"ok": True, "result": result}
