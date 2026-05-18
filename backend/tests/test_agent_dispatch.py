import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agent_dispatch import (  # noqa: E402
    check_tool_execution,
    tool_requires_confirmation,
)


def test_safe_tool_no_confirmation(monkeypatch):
    monkeypatch.setenv("AGENT_TOOL_AUTO_CONFIRM", "0")
    assert not tool_requires_confirmation("read_file", {})
    assert check_tool_execution("read_file", {}) is None


def test_dangerous_tool_blocks_without_confirm(monkeypatch):
    monkeypatch.setenv("AGENT_TOOL_AUTO_CONFIRM", "0")
    block = check_tool_execution("execute_python", {"code": "print(1)"})
    assert block is not None
    assert block["status"] == "confirm_required"
    assert block["risk_level"] == "dangerous"


def test_dangerous_tool_allows_with_confirmed(monkeypatch):
    monkeypatch.setenv("AGENT_TOOL_AUTO_CONFIRM", "0")
    assert check_tool_execution("execute_python", {"code": "1", "confirmed": True}) is None


def test_auto_confirm_env(monkeypatch):
    monkeypatch.setenv("AGENT_TOOL_AUTO_CONFIRM", "1")
    assert not tool_requires_confirmation("write_file", {})
