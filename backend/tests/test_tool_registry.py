import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from tool_registry import (  # noqa: E402
    TOOL_GROUPS,
    all_tool_names,
    get_tool_metadata,
    list_tool_metadata,
    validate_tool_registry,
)


def test_tool_registry_is_consistent():
    assert validate_tool_registry() == []


def test_tool_names_are_unique_and_grouped():
    names = all_tool_names()
    assert names
    assert len(names) == len(set(names))
    assert set(names) == {name for group in TOOL_GROUPS.values() for name in group}


def test_every_tool_has_ui_ready_metadata():
    for item in list_tool_metadata():
        assert item["name"]
        assert item["group"]
        assert item["description"]
        assert item["risk_level"] in {"safe", "confirm", "dangerous"}
        assert isinstance(item["timeout_seconds"], int)
        assert item["timeout_seconds"] > 0
        assert item["input_schema"]["type"] == "object"
        assert item["enabled"] is True


def test_representative_tool_metadata():
    read_file = get_tool_metadata("read_file")
    assert read_file["group"] == "files_code"
    assert read_file["risk_level"] == "safe"
    assert "path" in read_file["input_schema"].get("required", [])

    execute_python = get_tool_metadata("execute_python")
    assert execute_python["risk_level"] == "dangerous"
    assert "code" in execute_python["input_schema"].get("required", [])

    write_file = get_tool_metadata("write_file")
    assert write_file["risk_level"] == "confirm"
