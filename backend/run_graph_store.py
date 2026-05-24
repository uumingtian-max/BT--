"""Run graph persistence: runs / steps / artifacts / visual_events (SQLite).

Complements automation_store.automation_runs with step-level timeline and durable events.
"""

from __future__ import annotations

import json
import os
import sqlite_wal as sqlite3
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

DB_PATH = os.path.join(os.path.dirname(__file__), "run_graph.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def init_run_graph_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                kind TEXT NOT NULL,
                target TEXT NOT NULL DEFAULT 'all',
                job_id TEXT,
                status TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                meta_json TEXT NOT NULL DEFAULT '{}',
                started_at TEXT NOT NULL,
                ended_at TEXT,
                duration_ms INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_steps (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                detail_json TEXT NOT NULL DEFAULT '{}',
                started_at TEXT NOT NULL,
                ended_at TEXT,
                duration_ms INTEGER,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_artifacts (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                step_id TEXT,
                path TEXT NOT NULL DEFAULT '',
                kind TEXT NOT NULL DEFAULT 'log',
                meta_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS visual_events (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                type TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'info',
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_run_steps_run ON run_steps(run_id, seq)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_visual_events_created ON visual_events(created_at DESC)")
        conn.commit()


def begin_run(
    *,
    run_id: str,
    source: str,
    kind: str,
    target: str = "all",
    job_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    init_run_graph_db()
    now = _now_iso()
    with _conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO runs
            (id, source, kind, target, job_id, status, started_at, meta_json)
            VALUES (?, ?, ?, ?, ?, 'running', ?, ?)
            """,
            (
                run_id,
                source,
                kind,
                target or "all",
                job_id,
                now,
                json.dumps(meta or {}, ensure_ascii=False),
            ),
        )
        conn.commit()
    return get_run(run_id) or {}


def finish_run_graph(
    run_id: str,
    *,
    status: str,
    summary: str = "",
    duration_ms: int | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    init_run_graph_db()
    row = get_run(run_id)
    meta_json = json.dumps(meta or {}, ensure_ascii=False)
    if row and meta:
        try:
            merged = {**json.loads(row.get("meta_json") or "{}"), **meta}
            meta_json = json.dumps(merged, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
    with _conn() as conn:
        conn.execute(
            """
            UPDATE runs
            SET status=?, summary=?, ended_at=?, duration_ms=?, meta_json=?
            WHERE id=?
            """,
            (status, summary or "", _now_iso(), duration_ms, meta_json, run_id),
        )
        conn.commit()
    return get_run(run_id) or {}


def add_step(
    run_id: str,
    *,
    name: str,
    status: str,
    detail: dict[str, Any] | None = None,
    duration_ms: int | None = None,
    seq: int | None = None,
) -> dict[str, Any]:
    init_run_graph_db()
    step_id = str(uuid4())
    now = _now_iso()
    if seq is None:
        with _conn() as conn:
            cur = conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM run_steps WHERE run_id=?",
                (run_id,),
            )
            seq = int(cur.fetchone()[0])
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO run_steps
            (id, run_id, seq, name, status, detail_json, started_at, ended_at, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                step_id,
                run_id,
                int(seq),
                name,
                status,
                json.dumps(detail or {}, ensure_ascii=False),
                now,
                now,
                duration_ms,
            ),
        )
        conn.commit()
    return {"id": step_id, "run_id": run_id, "seq": seq, "name": name, "status": status}


def add_artifact(
    run_id: str,
    *,
    path: str = "",
    kind: str = "log",
    step_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    init_run_graph_db()
    artifact_id = str(uuid4())
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO run_artifacts (id, run_id, step_id, path, kind, meta_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                run_id,
                step_id,
                path or "",
                kind,
                json.dumps(meta or {}, ensure_ascii=False),
                _now_iso(),
            ),
        )
        conn.commit()
    return {"id": artifact_id, "run_id": run_id, "path": path, "kind": kind}


def append_visual_event(
    *,
    event_id: str,
    event_type: str,
    source: str,
    title: str,
    status: str = "info",
    payload: dict[str, Any] | None = None,
    run_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    init_run_graph_db()
    created = created_at or _now_iso()
    with _conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO visual_events
            (id, run_id, type, source, title, status, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                run_id,
                event_type,
                source,
                title,
                status,
                json.dumps(payload or {}, ensure_ascii=False),
                created,
            ),
        )
        conn.commit()
    return {
        "id": event_id,
        "run_id": run_id,
        "type": event_type,
        "source": source,
        "title": title,
        "status": status,
        "payload": payload or {},
        "created_at": created,
    }


def list_visual_events(
    *,
    limit: int = 100,
    source: str | None = None,
    run_id: str | None = None,
) -> list[dict[str, Any]]:
    init_run_graph_db()
    limit = max(1, min(500, int(limit or 100)))
    clauses: list[str] = []
    params: list[Any] = []
    if source:
        clauses.append("source=?")
        params.append(source)
    if run_id:
        clauses.append("run_id=?")
        params.append(run_id)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM visual_events{where} ORDER BY created_at DESC LIMIT ?",
            params,
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["payload"] = json.loads(item.pop("payload_json") or "{}")
        except json.JSONDecodeError:
            item["payload"] = {}
        out.append(item)
    return out


def get_run(run_id: str) -> dict[str, Any] | None:
    init_run_graph_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    if not row:
        return None
    data = dict(row)
    try:
        data["meta"] = json.loads(data.pop("meta_json") or "{}")
    except json.JSONDecodeError:
        data["meta"] = {}
    return data


def list_steps(run_id: str) -> list[dict[str, Any]]:
    init_run_graph_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM run_steps WHERE run_id=? ORDER BY seq ASC",
            (run_id,),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["detail"] = json.loads(item.pop("detail_json") or "{}")
        except json.JSONDecodeError:
            item["detail"] = {}
        out.append(item)
    return out


def list_artifacts(run_id: str) -> list[dict[str, Any]]:
    init_run_graph_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM run_artifacts WHERE run_id=? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["meta"] = json.loads(item.pop("meta_json") or "{}")
        except json.JSONDecodeError:
            item["meta"] = {}
        out.append(item)
    return out


def get_run_detail(run_id: str) -> dict[str, Any] | None:
    run = get_run(run_id)
    if not run:
        return None
    run["steps"] = list_steps(run_id)
    run["artifacts"] = list_artifacts(run_id)
    run["events"] = list_visual_events(limit=200, run_id=run_id)
    return run


def list_runs(*, limit: int = 50, source: str | None = None) -> list[dict[str, Any]]:
    init_run_graph_db()
    limit = max(1, min(200, int(limit or 50)))
    if source:
        with _conn() as conn:
            rows = conn.execute(
                "SELECT * FROM runs WHERE source=? ORDER BY started_at DESC LIMIT ?",
                (source, limit),
            ).fetchall()
    else:
        with _conn() as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["meta"] = json.loads(item.pop("meta_json") or "{}")
        except json.JSONDecodeError:
            item["meta"] = {}
        out.append(item)
    return out


def record_steps_from_result(run_id: str, result: dict[str, Any]) -> None:
    """Map automation runner step dicts into run_steps rows."""
    steps = result.get("steps")
    if isinstance(steps, list) and steps:
        for idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                continue
            label = str(step.get("label") or f"step_{idx}")
            ok = bool(step.get("ok"))
            add_step(
                run_id,
                name=label,
                status="success" if ok else "failed",
                detail=step,
                duration_ms=step.get("duration_ms"),
                seq=idx,
            )
            output = (step.get("output") or "").strip()
            if output:
                add_artifact(
                    run_id,
                    path=f"step:{label}",
                    kind="log",
                    meta={"output": output[-8000:]},
                )
        return
    label = str(result.get("label") or "task")
    ok = bool(result.get("ok", True))
    add_step(
        run_id,
        name=label,
        status="success" if ok else "failed",
        detail=result,
        duration_ms=result.get("duration_ms"),
        seq=1,
    )


init_run_graph_db()
