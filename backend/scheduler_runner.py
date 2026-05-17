"""Execute scheduled jobs and background tick loop."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

from agent_runtime import get_runtime
from scheduler_store import due_jobs, mark_job_run

logger = logging.getLogger(__name__)


async def run_job_now(job: dict[str, Any]) -> dict[str, Any]:
    kind = (job.get("task_kind") or "agent").strip().lower()
    message = (job.get("message") or "").strip()
    model = (job.get("model") or "").strip() or get_runtime().default_chat_model

    if kind == "habit_check":
        try:
            from habit_pipeline import run_habit_check

            phase = "evening" if "evening" in message.lower() else "morning"
            result = await asyncio.to_thread(run_habit_check, phase=phase)
            text = result.get("summary") or ""
            mark_job_run(str(job["id"]), int(job.get("interval_sec") or 86400))
            return {"ok": True, "text": text[:8000], "habit": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if not message:
        return {"ok": False, "error": "empty message"}

    text = ""
    try:
        if kind == "chat":
            from chat import get_history, save_message
            from llm_client import chat_complete_async

            sid = f"scheduler-{job.get('id', 'x')}"
            history = get_history(sid, limit=6)
            messages = history + [{"role": "user", "content": message}]
            text = await chat_complete_async(messages, model)
            save_message(sid, "user", message)
            save_message(sid, "assistant", text)
        else:
            from agent import run_agent

            steps = await run_agent(message, model)
            final = next((s for s in reversed(steps) if s.get("type") == "final_answer"), None)
            text = (final or {}).get("content") or str(steps[-1] if steps else "")
    except Exception as e:
        return {"ok": False, "error": str(e)}

    webhook = (job.get("delivery_webhook") or os.environ.get("SCHEDULER_WEBHOOK_URL") or "").strip()
    if webhook and text:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(
                    webhook,
                    json={
                        "job_id": job.get("id"),
                        "name": job.get("name"),
                        "result": text[:8000],
                    },
                )
        except Exception as e:
            logger.warning("scheduler webhook failed: %s", e)

    mark_job_run(str(job["id"]), int(job.get("interval_sec") or 3600))
    return {"ok": True, "text": text[:8000]}


async def background_scheduler_loop() -> None:
    if os.environ.get("SCHEDULER_ENABLED", "1").strip() in ("0", "false", "off"):
        return
    tick = max(15, int(os.environ.get("SCHEDULER_TICK_SEC", "30") or 30))
    while True:
        try:
            for job in due_jobs():
                try:
                    await run_job_now(job)
                except Exception as e:
                    logger.exception("scheduler job %s failed: %s", job.get("id"), e)
        except Exception as e:
            logger.exception("scheduler tick: %s", e)
        await asyncio.sleep(tick)
