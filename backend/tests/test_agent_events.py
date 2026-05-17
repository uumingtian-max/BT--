import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_events import normalize_agent_step, normalize_agent_steps, timeline_contract  # noqa: E402


def test_normalize_tool_call_adds_risk_level():
    event = normalize_agent_step(
        {"type": "tool_call", "tool": "execute_python", "params": {"code": "print(1)"}},
        run_id="run-1",
        index=0,
    )
    assert event["run_id"] == "run-1"
    assert event["index"] == 0
    assert event["type"] == "tool_call"
    assert event["status"] == "running"
    assert event["tool"] == "execute_python"
    assert event["risk_level"] == "dangerous"
    assert event["params"] == {"code": "print(1)"}
    assert event["step_id"]
    assert event["created_at"].endswith("Z")


def test_normalize_tool_result_detects_failure():
    event = normalize_agent_step(
        {"type": "tool_result", "tool": "read_file", "result": "Tool error: not found"},
        run_id="run-1",
        index=1,
    )
    assert event["type"] == "tool_result"
    assert event["status"] == "failed"
    assert event["risk_level"] == "safe"


def test_normalize_unknown_step_falls_back_to_thinking():
    event = normalize_agent_step({"type": "custom", "content": "hello"}, run_id="run-1", index=2)
    assert event["type"] == "thinking"
    assert event["content"] == "hello"


def test_normalize_steps_reuses_run_id():
    events = normalize_agent_steps(
        [
            {"type": "thinking", "content": "plan"},
            {"type": "final_answer", "content": "done"},
        ],
        run_id="run-x",
    )
    assert [event["run_id"] for event in events] == ["run-x", "run-x"]
    assert [event["index"] for event in events] == [0, 1]


def test_timeline_contract_is_ui_ready():
    contract = timeline_contract()
    event_types = {item["type"] for item in contract["event_types"]}
    assert {"thinking", "tool_call", "tool_result", "final_answer"}.issubset(event_types)
    assert "schema" in contract
    assert "dangerous" in contract["risk_values"]
