"""Persistent run graph store for Agent and automation traces.

The first version is intentionally small and local-first. It gives the UI a
stable SQLite-backed shape for runs, steps, artifacts, and visual events while
keeping the existing automation_store tables compatible.
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


def _json_dumps(value: Any) -> str:
    try:
        return json.dumps(value if value is not None else {}, ensure_ascii=False)
    except TypeError:
        return json.dumps({"repr": repr(value)}, ensure_ascii=False)


def _json_loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def init_run_graph_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                target TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'running',
                summary TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
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
                parent_step_id TEXT,
                step_index INTEGER NOT NULL,
                step_type TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                input_json TEXT NOT NULL DEFAULT '{}',
                output_json TEXT NOT NULL DEFAULT '{}',
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
                artifact_type TEXT NOT NULL,
                title TEXT NOT NULL,
                path TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id),
                FOREIGN KEY(step_id) REFERENCES run_steps(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS visual_events (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'info',
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_run_steps_run_id ON run_steps(run_id, step_index)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_source_status ON runs(source, status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_visual_events_source ON visual_events(source, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_visual_events_run ON visual_events(run_id, created_at)")
        conn.commit()


def start_run_graph(
    *,
    source: str,
    kind: str,
    title: str = "",
    target: str = "",
    run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a run graph record and return it.

    ``run_id`` may be supplied by existing systems such as automation_store so
    older API responses and the new run graph share the same identifier.
    """
    init_run_graph_db()
    rid = run_id or str(uuid4())
    now = _now_iso()
    with _conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO runs
                (id, source, kind, title, target, status, summary, metadata_json, started_at, ended_at, duration_ms)
            VALUES (?, ?, ?, ?, ?, 'running', '', ?, ?, NULL, NULL)
            """,
            (
                rid,
                source.strip() or "unknown",
                kind.strip() or "task",
                title.strip() or kind.strip() or "task",
                target.strip() if target else "",
                _json_dumps(metadata or {}),
                now,
            ),
        )
        conn.commit()
    return get_run_graph(rid) or {}


def finish_run_graph(
    run_id: str,
    *,
    status: str,
    summary: str = "",
    duration_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    init_run_graph_db()
    with _conn() as conn:
        if metadata is None:
            conn.execute(
                """
                UPDATE runs
                SET status=?, summary=?, ended_at=?, duration_ms=?
                WHERE id=?
                """,
                (status, summary or "", _now_iso(), duration_ms, run_id),
            )
        else:
            conn.execute(
                """
                UPDATE runs
                SET status=?, summary=?, metadata_json=?, ended_at=?, duration_ms=?
                WHERE id=?
                """,
                (status, summary or "", _json_dumps(metadata), _now_iso(), duration_ms, run_id),
            )
        conn.commit()
    return get_run_graph(run_id) or {}


def add_run_step(
    *,
    run_id: str,
    step_type: str,
    name: str,
    status: str = "success",
    input_data: dict[str, Any] | None = None,
    output_data: dict[str, Any] | None = None,
    parent_step_id: str | None = None,
    duration_ms: int | None = None,
    step_id: str | None = None,
) -> dict[str, Any]:
    init_run_graph_db()
    sid = step_id or str(uuid4())
    now = _now_iso()
    ended_at = now if status != "running" else None
    with _conn() as conn:
        row = conn.execute("SELECT COALESCE(MAX(step_index), -1) + 1 FROM run_steps WHERE run_id=?", (run_id,)).fetchone()
        step_index = int(row[0] if row else 0)
        conn.execute(
            """
            INSERT INTO run_steps
                (id, run_id, parent_step_id, step_index, step_type, name, status,
                 input_json, output_json, started_at, ended_at, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sid,
                run_id,
                parent_step_id,
                step_index,
                step_type.strip() or "step",
                name.strip() or step_type.strip() or "step",
                status.strip() or "success",
                _json_dumps(input_data or {}),
                _json_dumps(output_data or {}),
                now,
                ended_at,
                duration_ms,
            ),
        )
        conn.commit()
    return get_run_step(sid) or {}


def finish_run_step(
    step_id: str,
    *,
    status: str,
    output_data: dict[str, Any] | None = None,
    duration_ms: int | None = None,
) -> dict[str, Any] | None:
    init_run_graph_db()
    with _conn() as conn:
        conn.execute(
            """
            UPDATE run_steps
            SET status=?, output_json=?, ended_at=?, duration_ms=?
            WHERE id=?
            """,
            (status, _json_dumps(output_data or {}), _now_iso(), duration_ms, step_id),
        )
        conn.commit()
    return get_run_step(step_id)


def add_run_artifact(
    *,
    run_id: str,
    artifact_type: str,
    title: str,
    step_id: str | None = None,
    path: str = "",
    url: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    init_run_graph_db()
    artifact_id = str(uuid4())
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO run_artifacts
                (id, run_id, step_id, artifact_type, title, path, url, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                run_id,
                step_id,
                artifact_type.strip() or "file",
                title.strip() or artifact_type.strip() or "artifact",
                path,
                url,
                _json_dumps(metadata or {}),
                _now_iso(),
            ),
        )
        conn.commit()
    return get_run_artifact(artifact_id) or {}


def store_visual_event(event: dict[str, Any]) -> dict[str, Any]:
    init_run_graph_db()
    event_id = str(event.get("id") or uuid4())
    created_at = str(event.get("created_at") or _now_iso())
    with _conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO visual_events
                (id, run_id, event_type, source, title, status, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event.get("run_id"),
                str(event.get("type") or event.get("event_type") or "event"),
                str(event.get("source") or "unknown"),
                str(event.get("title") or ""),
                str(event.get("status") or "info"),
                _json_dumps(event.get("payload") or {}),
                created_at,
            ),
        )
        conn.commit()
    return get_visual_event(event_id) or {}


def _decode_run(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["metadata"] = _json_loads(item.pop("metadata_json", "{}"), {})
    return item


def _decode_step(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["input"] = _json_loads(item.pop("input_json", "{}"), {})
    item["output"] = _json_loads(item.pop("output_json", "{}"), {})
    return item


def _decode_artifact(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["metadata"] = _json_loads(item.pop("metadata_json", "{}"), {})
    return item


def _decode_event(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["type"] = item.pop("event_type")
    item["payload"] = _json_loads(item.pop("payload_json", "{}"), {})
    return item


def get_run_graph(run_id: str, *, include_steps: bool = True, include_artifacts: bool = True) -> dict[str, Any] | None:
    init_run_graph_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            return None
        run = _decode_run(row)
        if include_steps:
            steps = conn.execute(
                "SELECT * FROM run_steps WHERE run_id=? ORDER BY step_index ASC",
                (run_id,),
            ).fetchall()
            run["steps"] = [_decode_step(step) for step in steps]
        if include_artifacts:
            artifacts = conn.execute(
                "SELECT * FROM run_artifacts WHERE run_id=? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
            run["artifacts"] = [_decode_artifact(artifact) for artifact in artifacts]
    return run


def get_run_step(step_id: str) -> dict[str, Any] | None:
    init_run_graph_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM run_steps WHERE id=?", (step_id,)).fetchone()
    return _decode_step(row) if row else None


def get_run_artifact(artifact_id: str) -> dict[str, Any] | None:
    init_run_graph_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM run_artifacts WHERE id=?", (artifact_id,)).fetchone()
    return _decode_artifact(row) if row else None


def get_visual_event(event_id: str) -> dict[str, Any] | None:
    init_run_graph_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM visual_events WHERE id=?", (event_id,)).fetchone()
    return _decode_event(row) if row else None


def list_run_graphs(*, limit: int = 50, source: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    init_run_graph_db()
    limit = max(1, min(200, int(limit or 50)))
    clauses: list[str] = []
    params: list[Any] = []
    if source:
        clauses.append("source=?")
        params.append(source)
    if status:
        clauses.append("status=?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM runs {where} ORDER BY started_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
    return [_decode_run(row) for row in rows]


def list_visual_events(*, limit: int = 100, source: str | None = None, run_id: str | None = None) -> list[dict[str, Any]]:
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
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM visual_events {where} ORDER BY created_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
    return [_decode_event(row) for row in rows]


init_run_graph_db()
