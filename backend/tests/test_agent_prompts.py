import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_prompts import TOOLS_DESC, build_tools_desc  # noqa: E402
from tool_registry import TOOL_DESCRIPTIONS, all_tool_names, validate_tool_registry  # noqa: E402


def test_tools_desc_lists_all_registry_tools():
    assert validate_tool_registry() == []
    for name in all_tool_names():
        assert name in TOOLS_DESC
        assert TOOL_DESCRIPTIONS[name] in TOOLS_DESC


def test_build_tools_desc_idempotent():
    assert build_tools_desc() == TOOLS_DESC
