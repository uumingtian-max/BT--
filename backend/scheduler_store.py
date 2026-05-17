"""SQLite-backed scheduled jobs (interval-based agent/chat tasks)."""

from __future__ import annotations

import os
import sqlite_wal as sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

DB_PATH = os.path.join(os.path.dirname(__file__), "scheduler.db")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_scheduler_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                interval_sec INTEGER NOT NULL DEFAULT 3600,
                task_kind TEXT NOT NULL DEFAULT 'agent',
                message TEXT NOT NULL,
                model TEXT,
                delivery_webhook TEXT,
                last_run_at TEXT,
                next_run_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def list_jobs() -> list[dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM scheduled_jobs ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_job(job_id: str) -> dict[str, Any] | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM scheduled_jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row) if row else None


def create_job(
    *,
    name: str,
    message: str,
    interval_sec: int = 3600,
    task_kind: str = "agent",
    model: str | None = None,
    delivery_webhook: str | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    jid = str(uuid.uuid4())
    interval_sec = max(60, int(interval_sec))
    next_at = (datetime.now(timezone.utc) + timedelta(seconds=interval_sec)).replace(microsecond=0).isoformat()
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO scheduled_jobs
            (id, name, enabled, interval_sec, task_kind, message, model, delivery_webhook, next_run_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                jid,
                name.strip() or "scheduled",
                1 if enabled else 0,
                interval_sec,
                task_kind,
                message,
                model,
                delivery_webhook,
                next_at,
            ),
        )
        conn.commit()
    return get_job(jid) or {}


def delete_job(job_id: str) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM scheduled_jobs WHERE id=?", (job_id,))
        conn.commit()
        return cur.rowcount > 0


def set_job_enabled(job_id: str, enabled: bool) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE scheduled_jobs SET enabled=? WHERE id=?",
            (1 if enabled else 0, job_id),
        )
        conn.commit()
        return cur.rowcount > 0


def due_jobs() -> list[dict[str, Any]]:
    now = _now_iso()
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM scheduled_jobs
            WHERE enabled=1 AND (next_run_at IS NULL OR next_run_at <= ?)
            ORDER BY next_run_at ASC
            LIMIT 20
            """,
            (now,),
        ).fetchall()
    return [dict(r) for r in rows]


init_scheduler_db()


def mark_job_run(job_id: str, interval_sec: int) -> None:
    now = _now_iso()
    nxt = (datetime.now(timezone.utc) + timedelta(seconds=max(60, interval_sec))).replace(microsecond=0).isoformat()
    with _conn() as conn:
        conn.execute(
            "UPDATE scheduled_jobs SET last_run_at=?, next_run_at=? WHERE id=?",
            (now, nxt, job_id),
        )
        conn.commit()
