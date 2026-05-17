"""SQLite store for local automation jobs and runs."""

from __future__ import annotations

import os
import sqlite_wal as sqlite3
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

DB_PATH = os.path.join(os.path.dirname(__file__), "automation.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def init_automation_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automation_jobs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                task_kind TEXT NOT NULL,
                target TEXT NOT NULL DEFAULT 'all',
                enabled INTEGER NOT NULL DEFAULT 1,
                params_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automation_runs (
                id TEXT PRIMARY KEY,
                job_id TEXT,
                task_kind TEXT NOT NULL,
                target TEXT NOT NULL DEFAULT 'all',
                status TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                result_json TEXT NOT NULL DEFAULT '{}',
                started_at TEXT NOT NULL,
                ended_at TEXT,
                duration_ms INTEGER,
                FOREIGN KEY(job_id) REFERENCES automation_jobs(id)
            )
            """
        )
        conn.commit()


def list_jobs() -> list[dict[str, Any]]:
    init_automation_db()
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM automation_jobs ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def create_job(
    *,
    name: str,
    task_kind: str,
    target: str = "all",
    params_json: str = "{}",
    enabled: bool = True,
) -> dict[str, Any]:
    init_automation_db()
    now = _now_iso()
    job_id = str(uuid4())
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO automation_jobs (id, name, task_kind, target, enabled, params_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                name.strip() or task_kind,
                task_kind,
                target or "all",
                1 if enabled else 0,
                params_json or "{}",
                now,
                now,
            ),
        )
        conn.commit()
    return get_job(job_id) or {}


def get_job(job_id: str) -> dict[str, Any] | None:
    init_automation_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM automation_jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row) if row else None


def delete_job(job_id: str) -> bool:
    init_automation_db()
    with _conn() as conn:
        cur = conn.execute("DELETE FROM automation_jobs WHERE id=?", (job_id,))
        conn.commit()
        return cur.rowcount > 0


def set_job_enabled(job_id: str, enabled: bool) -> bool:
    init_automation_db()
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE automation_jobs SET enabled=?, updated_at=? WHERE id=?",
            (1 if enabled else 0, _now_iso(), job_id),
        )
        conn.commit()
        return cur.rowcount > 0


def start_run(*, task_kind: str, target: str = "all", job_id: str | None = None) -> dict[str, Any]:
    init_automation_db()
    run_id = str(uuid4())
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO automation_runs (id, job_id, task_kind, target, status, started_at)
            VALUES (?, ?, ?, ?, 'running', ?)
            """,
            (run_id, job_id, task_kind, target or "all", _now_iso()),
        )
        conn.commit()
    return get_run(run_id) or {}


def finish_run(
    run_id: str,
    *,
    status: str,
    summary: str,
    result_json: str = "{}",
    duration_ms: int | None = None,
) -> dict[str, Any]:
    init_automation_db()
    with _conn() as conn:
        conn.execute(
            """
            UPDATE automation_runs
            SET status=?, summary=?, result_json=?, ended_at=?, duration_ms=?
            WHERE id=?
            """,
            (
                status,
                summary or "",
                result_json or "{}",
                _now_iso(),
                duration_ms,
                run_id,
            ),
        )
        conn.commit()
    return get_run(run_id) or {}


def get_run(run_id: str) -> dict[str, Any] | None:
    init_automation_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM automation_runs WHERE id=?", (run_id,)).fetchone()
    return dict(row) if row else None


def list_runs(*, limit: int = 50) -> list[dict[str, Any]]:
    init_automation_db()
    limit = max(1, min(200, int(limit or 50)))
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM automation_runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


init_automation_db()
