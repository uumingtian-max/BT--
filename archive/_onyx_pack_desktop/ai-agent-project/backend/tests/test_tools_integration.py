"""Verify backend/tools/* are wired into agent.TOOL_MAP and basic smoke behavior."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from agent import TOOL_MAP, _normalize_parsed_tool  # noqa: E402
from tools import __all__ as tools_exports  # noqa: E402


EXPECTED_TOOL_MODULES = {
    "web_search": "tools.search",
    "local_search": "tools.local_crawl",
    "local_scrape_url": "tools.local_crawl",
    "read_file": "tools.file_ops",
    "write_file": "tools.file_ops",
    "list_files": "tools.file_ops",
    "execute_python": "tools.code_exec",
    "open_url": "tools.external_control",
    "open_path": "tools.external_control",
    "get_foreground_window": "tools.external_control",
    "list_windows": "tools.external_control",
    "focus_window": "tools.external_control",
    "send_hotkey": "tools.external_control",
    "type_text": "tools.external_control",
    "click_screen": "tools.external_control",
    "browser_navigate": "tools.browser",
    "browser_playwright": "tools.browser",
    "run_parallel_subagents": "subagent_runner",
}


def test_tools_package_exports():
    for name in (
        "web_search",
        "local_search",
        "local_scrape_url",
        "read_file",
        "write_file",
        "list_files",
        "execute_python",
        "open_url",
        "browser_playwright",
    ):
        assert name in tools_exports


def test_core_tools_in_tool_map():
    for name in EXPECTED_TOOL_MODULES:
        assert name in TOOL_MAP, f"missing TOOL_MAP entry: {name}"


def test_agent_tools_http(client):
    r = client.get("/agent/tools")
    assert r.status_code == 200
    body = r.json()
    assert body.get("count", 0) >= len(EXPECTED_TOOL_MODULES)
    for name in EXPECTED_TOOL_MODULES:
        assert name in body.get("tools", [])


def test_normalize_flat_query_field():
    raw = {"name": "web_search", "query": "AI news"}
    out = _normalize_parsed_tool(raw)
    assert out["parameters"]["query"] == "AI news"


def test_model_download_research_uses_search_not_download_folder():
    from agent import infer_tool_from_message

    msg = "帮我看看目前最牛逼的顶级模型可以下载的本地 适配GPU5090/24G"
    tool = infer_tool_from_message(msg)
    assert tool is not None
    assert tool["name"] == "local_search"
    assert tool["parameters"]["scrape"] is True
    assert "GPU5090" in tool["parameters"]["query"]


def test_execute_python_smoke():
    fn = TOOL_MAP["execute_python"]
    out = fn({"code": "print(2+2)"})
    assert "4" in out


def test_list_files_desktop_smoke():
    fn = TOOL_MAP["list_files"]
    out = fn({"directory": "~/Desktop"})
    assert "[PATH]" in out or "Not found" in out


def test_sqlite_wal_helper_enables_wal(tmp_path):
    import sqlite_wal as sqlite3

    db_path = tmp_path / "wal-smoke.db"
    conn = sqlite3.connect(db_path)
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    finally:
        conn.close()
    assert str(mode).lower() == "wal"


def test_local_scrape_invalid_url():
    fn = TOOL_MAP["local_scrape_url"]
    out = fn({"url": "not-a-url"})
    assert "error" in out.lower()


def test_web_search_missing_query():
    from agent import _web_search_tool

    out = _web_search_tool({})
    assert "error" in out.lower() or "缺少" in out


def test_web_search_live_optional():
  """Runs when INTEGRATION_NETWORK=1 (e.g. local verify script)."""
  import os

  if os.environ.get("INTEGRATION_NETWORK") != "1":
      pytest.skip("set INTEGRATION_NETWORK=1 to run live search")
  from tools.search import web_search

  out = web_search("Python programming language")
  assert out and len(out) > 20
