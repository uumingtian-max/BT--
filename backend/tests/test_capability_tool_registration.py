import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_tool_map import TOOL_MAP  # noqa: E402
from tool_registry import get_tool_metadata, validate_tool_registry  # noqa: E402


def test_capability_route_tool_is_registered_in_tool_map_and_registry():
    assert "route_capability_intent" in TOOL_MAP
    assert validate_tool_registry() == []

    meta = get_tool_metadata("route_capability_intent")
    assert meta["group"] == "capability_control"
    assert meta["risk_level"] == "safe"
    assert "message" in meta["input_schema"].get("required", [])


def test_capability_route_tool_returns_plan_json():
    raw = TOOL_MAP["route_capability_intent"]({"message": "屏幕太刺眼，开护眼模式"})
    assert "system.eye_comfort" in raw
    assert "environment_comfort" in raw
