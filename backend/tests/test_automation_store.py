import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import automation_store  # noqa: E402


def test_automation_job_and_run_lifecycle(tmp_path):
    old_path = automation_store.DB_PATH
    automation_store.DB_PATH = os.path.join(tmp_path, "automation.db")
    try:
        automation_store.init_automation_db()
        job = automation_store.create_job(name="健康检查", task_kind="repo_health", target="all")
        assert job["id"]
        assert job["enabled"] == 1
        assert automation_store.get_job(job["id"])["task_kind"] == "repo_health"

        assert len(automation_store.list_jobs()) == 1
        assert automation_store.set_job_enabled(job["id"], False) is True
        assert automation_store.get_job(job["id"])["enabled"] == 0

        run = automation_store.start_run(task_kind="repo_health", target="all", job_id=job["id"])
        assert run["status"] == "running"
        finished = automation_store.finish_run(run["id"], status="success", summary="ok", result_json='{"ok": true}', duration_ms=12)
        assert finished["status"] == "success"
        assert finished["summary"] == "ok"
        assert finished["duration_ms"] == 12
        assert len(automation_store.list_runs()) == 1

        assert automation_store.delete_job(job["id"]) is True
    finally:
        automation_store.DB_PATH = old_path
