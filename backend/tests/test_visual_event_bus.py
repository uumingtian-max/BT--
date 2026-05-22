import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from visual_event_bus import clear_events, list_events, publish_event  # noqa: E402


def test_visual_event_bus_publish_and_filter(monkeypatch):
    monkeypatch.setenv("RUN_GRAPH_TEST_CLEAR", "1")
    clear_events()
    first = publish_event(
        event_type="automation_run_started",
        source="automation",
        title="started",
        run_id="run-1",
        status="running",
        payload={"target": "all"},
    )
    publish_event(
        event_type="agent_step",
        source="agent",
        title="agent",
        run_id="run-2",
        status="success",
    )

    assert first["id"]
    assert first["created_at"].endswith("Z")
    assert len(list_events()) == 2
    assert [e["source"] for e in list_events(source="automation")] == ["automation"]
    assert [e["run_id"] for e in list_events(run_id="run-1")] == ["run-1"]
