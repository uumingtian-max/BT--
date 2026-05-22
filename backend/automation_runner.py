"""Local automation runner for BT (Heiguang).

This runner intentionally starts with a conservative allow-list of maintenance
jobs. It powers the Automation Dashboard without exposing an arbitrary command
runner. Each run is also mirrored into run_graph_store so the UI can render a
persistent timeline after restart.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from automation_store import finish_run, start_run
from run_graph_store import add_run_step, finish_run_graph, start_run_graph
from visual_event_bus import publish_event

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

ALLOWED_TASK_KINDS = {
    "project_check",
    "backend_compile",
    "frontend_build",
    "repo_health",
}
ALLOWED_TARGETS = {"all", "backend", "frontend"}


def automation_capabilities() -> dict[str, Any]:
    """Return tasks the Automation Dashboard may offer."""
    return {
        "task_kinds": sorted(ALLOWED_TASK_KINDS),
        "targets": sorted(ALLOWED_TARGETS),
        "default_task_kind": "project_check",
        "default_target": "all",
    }


def normalize_task_kind(task_kind: str | None) -> str:
    value = (task_kind or "project_check").strip().lower()
    if value not in ALLOWED_TASK_KINDS:
        raise ValueError(f"unsupported automation task_kind: {value}")
    return value


def normalize_target(target: str | None) -> str:
    value = (target or "all").strip().lower()
    if value not in ALLOWED_TARGETS:
        raise ValueError(f"unsupported automation target: {value}")
    return value


def run_automation_task(
    *, task_kind: str = "project_check", target: str = "all", job_id: str | None = None
) -> dict[str, Any]:
    """Run one maintenance automation synchronously and persist the run."""
    task_kind = normalize_task_kind(task_kind)
    target = normalize_target(target)
    started = time.perf_counter()
    run = start_run(task_kind=task_kind, target=target, job_id=job_id)
    run_id = run["id"]
    start_run_graph(
        source="automation",
        kind=task_kind,
        title=f"自动化任务：{task_kind}",
        target=target,
        run_id=run_id,
        metadata={"job_id": job_id, "target": target},
    )
    publish_event(
        event_type="automation_run_started",
        source="automation",
        title=f"开始自动化任务：{task_kind}",
        payload={"task_kind": task_kind, "target": target},
        run_id=run_id,
        status="running",
    )

    try:
        result = _execute_allowed_task(task_kind, target, run_id=run_id)
        status = "success" if result.get("ok") else "failed"
        summary = result.get("summary") or _default_summary(task_kind, status)
    except Exception as exc:  # defensive: convert crashes into visible run failures
        result = {"ok": False, "error": str(exc), "steps": []}
        status = "failed"
        summary = f"自动化任务失败：{exc}"
        add_run_step(
            run_id=run_id,
            step_type="error",
            name="automation_exception",
            status="failed",
            output_data={"error": str(exc)},
        )

    duration_ms = int((time.perf_counter() - started) * 1000)
    stored = finish_run(
        run_id,
        status=status,
        summary=summary,
        result_json=json.dumps(result, ensure_ascii=False),
        duration_ms=duration_ms,
    )
    run_graph = finish_run_graph(
        run_id,
        status=status,
        summary=summary,
        duration_ms=duration_ms,
        metadata={"job_id": job_id, "target": target, "result_ok": bool(result.get("ok"))},
    )
    publish_event(
        event_type="automation_run_finished",
        source="automation",
        title=summary,
        payload={"status": status, "duration_ms": duration_ms, "result": result},
        run_id=run_id,
        status=status,
    )
    stored["result"] = result
    stored["run_graph"] = run_graph
    return stored


def _execute_allowed_task(task_kind: str, target: str, *, run_id: str | None = None) -> dict[str, Any]:
    if task_kind == "backend_compile":
        return _backend_compile(run_id=run_id)
    if task_kind == "frontend_build":
        return _frontend_build(run_id=run_id)
    if task_kind == "repo_health":
        return _repo_health(run_id=run_id)
    if task_kind == "project_check":
        steps: list[dict[str, Any]] = []
        if target in ("all", "backend"):
            steps.append(_backend_compile(run_id=run_id))
        if target in ("all", "frontend"):
            steps.append(_frontend_build(run_id=run_id))
        ok = all(step.get("ok") for step in steps)
        return {
            "ok": ok,
            "summary": "项目检查通过" if ok else "项目检查发现问题",
            "steps": steps,
        }
    raise ValueError(f"unsupported automation task_kind: {task_kind}")


def _backend_compile(*, run_id: str | None = None) -> dict[str, Any]:
    files = [
        "main.py",
        "agent.py",
        "env_bootstrap.py",
        "tool_registry.py",
        "agent_run_events.py",
        "automation_store.py",
        "run_graph_store.py",
    ]
    return _run_command(
        label="backend_compile",
        cmd=[sys.executable, "-m", "py_compile", *files],
        cwd=BACKEND_DIR,
        timeout=120,
        run_id=run_id,
    )


def _frontend_build(*, run_id: str | None = None) -> dict[str, Any]:
    npm = "npm.cmd" if sys.platform.startswith("win") else "npm"
    return _run_command(
        label="frontend_build",
        cmd=[npm, "run", "build"],
        cwd=FRONTEND_DIR,
        timeout=240,
        run_id=run_id,
    )


def _repo_health(*, run_id: str | None = None) -> dict[str, Any]:
    steps = [
        _run_command("git_status", ["git", "status", "--short"], ROOT, timeout=30, run_id=run_id),
        _run_command("git_branch", ["git", "branch", "--show-current"], ROOT, timeout=30, run_id=run_id),
    ]
    ok = all(step.get("ok") for step in steps)
    return {
        "ok": ok,
        "summary": "仓库状态检查通过" if ok else "仓库状态检查失败",
        "steps": steps,
    }


def _run_command(label: str, cmd: list[str], cwd: Path, *, timeout: int, run_id: str | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    publish_event(
        event_type="automation_step_started",
        source="automation",
        title=f"运行步骤：{label}",
        payload={"label": label, "cmd": cmd, "cwd": str(cwd)},
        run_id=run_id,
        status="running",
    )
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = ((completed.stdout or "") + (("\nSTDERR:\n" + completed.stderr) if completed.stderr else "")).strip()
        result = {
            "label": label,
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "output": output[-6000:] if output else "",
        }
    except Exception as exc:
        result = {
            "label": label,
            "ok": False,
            "exit_code": None,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "output": str(exc),
        }
    status = "success" if result.get("ok") else "failed"
    if run_id:
        add_run_step(
            run_id=run_id,
            step_type="command",
            name=label,
            status=status,
            input_data={"cmd": cmd, "cwd": str(cwd), "timeout": timeout},
            output_data=result,
            duration_ms=result.get("duration_ms"),
        )
    publish_event(
        event_type="automation_step_finished",
        source="automation",
        title=f"步骤完成：{label}",
        payload=result,
        run_id=run_id,
        status=status,
    )
    return result


def _default_summary(task_kind: str, status: str) -> str:
    return f"{task_kind} {'完成' if status == 'success' else '失败'}"
