import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_run_events import (
    enrich_legacy_steps,
    event_from_legacy_step,
    summarize_timeline,
)  # noqa: E402


def test_event_from_tool_call_has_timeline_metadata():
    event = event_from_legacy_step(
        {"type": "tool_call", "tool": "read_file", "params": {"path": "README.md"}},
        run_id="run-1",
        index=0,
        timestamp="2026-05-17T00:00:00Z",
    )

    assert event["run_id"] == "run-1"
    assert event["index"] == 0
    assert event["event_type"] == "tool_call"
    assert event["status"] == "running"
    assert event["risk_level"] == "safe"
    assert event["tool_group"] == "files_code"
    assert event["tool"] == "read_file"
    assert event["tool_input_schema"]["type"] == "object"
    assert event["started_at"] == "2026-05-17T00:00:00Z"
    assert event["ended_at"] is None


def test_tool_result_error_is_marked_failed():
    event = event_from_legacy_step(
        {
            "type": "tool_result",
            "tool": "execute_python",
            "result": "Tool error: timeout",
        },
        run_id="run-1",
        index=1,
        timestamp="2026-05-17T00:00:01Z",
    )

    assert event["status"] == "failed"
    assert event["risk_level"] == "dangerous"
    assert event["ended_at"] == "2026-05-17T00:00:01Z"


def test_enrich_legacy_steps_preserves_legacy_fields():
    steps = [
        {"type": "thinking", "content": "plan"},
        {"type": "final_answer", "content": "done"},
    ]
    events = enrich_legacy_steps(steps, run_id="run-2")

    assert len(events) == 2
    assert events[0]["content"] == "plan"
    assert events[1]["content"] == "done"
    assert {event["run_id"] for event in events} == {"run-2"}
    assert all(event["step_id"] for event in events)


def test_summarize_timeline_counts_tools_and_risks():
    events = enrich_legacy_steps(
        [
            {"type": "tool_call", "tool": "read_file", "params": {"path": "README.md"}},
            {"type": "tool_result", "tool": "read_file", "result": "ok"},
            {
                "type": "tool_call",
                "tool": "write_file",
                "params": {"path": "x", "content": "y"},
            },
            {"type": "final_answer", "content": "done"},
        ],
        run_id="run-3",
    )
    summary = summarize_timeline(events)

    assert summary["run_id"] == "run-3"
    assert summary["step_count"] == 4
    assert summary["tool_call_count"] == 2
    assert summary["unique_tools"] == ["read_file", "write_file"]
    assert summary["has_final_answer"] is True
    assert summary["risk_counts"]["safe"] >= 2
    assert summary["risk_counts"]["confirm"] >= 1
