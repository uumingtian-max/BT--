"""Integration-style tests for agent tool loop policy (no live LLM)."""

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_dispatch import execute_tool_sync  # noqa: E402


def test_execute_tool_sync_runs_handler():
    tool_map = {"echo": lambda p: f"ok:{p.get('x')}"}
    out = execute_tool_sync("echo", {"x": "1"}, tool_map)
    assert out == "ok:1"


def test_execute_tool_sync_blocks_unconfirmed_dangerous(monkeypatch):
    monkeypatch.setenv("AGENT_TOOL_AUTO_CONFIRM", "0")
    tool_map = {"execute_python": lambda p: "ran"}
    out = execute_tool_sync("execute_python", {"code": "1"}, tool_map)
    assert "confirmed" in out.lower() or "确认" in out
