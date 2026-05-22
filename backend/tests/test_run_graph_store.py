from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture()
def graph_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = tmp_path / "run_graph_test.db"
    monkeypatch.setattr("run_graph_store.DB_PATH", str(db))
    import run_graph_store

    run_graph_store.init_run_graph_db()
    yield db


def test_begin_finish_run_and_steps(graph_db: Path) -> None:
    import run_graph_store as rg

    rg.begin_run(run_id="r1", source="automation", kind="project_check", target="all")
    rg.record_steps_from_result(
        "r1",
        {
            "ok": True,
            "steps": [
                {"label": "backend_compile", "ok": True, "duration_ms": 10, "output": "ok"},
                {"label": "frontend_build", "ok": False, "duration_ms": 20, "output": "fail"},
            ],
        },
    )
    rg.finish_run_graph("r1", status="failed", summary="检查失败", duration_ms=30)
    detail = rg.get_run_detail("r1")
    assert detail is not None
    assert detail["status"] == "failed"
    assert len(detail["steps"]) == 2
    assert detail["steps"][0]["name"] == "backend_compile"
    assert len(detail["artifacts"]) >= 1


def test_visual_events_persist(graph_db: Path) -> None:
    import run_graph_store as rg
    from visual_event_bus import clear_events, list_events, publish_event

    clear_events()
    publish_event(
        event_type="test_pulse",
        source="automation",
        title="测试事件",
        run_id="r2",
        status="info",
    )
    rows = rg.list_visual_events(limit=10, source="automation")
    assert any(e.get("title") == "测试事件" for e in rows)
    merged = list_events(limit=10, source="automation")
    assert any(e.get("title") == "测试事件" for e in merged)
