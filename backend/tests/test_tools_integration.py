"""Verify backend/tools/* are wired into agent.TOOL_MAP and basic smoke behavior."""

from __future__ import annotations

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


def test_generate_ai_video_registered():
    assert "generate_ai_video" in TOOL_MAP
    assert callable(TOOL_MAP["generate_ai_video"])


def test_infer_generate_ai_video():
    from agent import infer_tool_from_message

    tool = infer_tool_from_message("帮我生成一段视频：海边日落航拍")
    assert tool is not None
    assert tool["name"] == "generate_ai_video"
    assert tool["parameters"]["prompt"]
    assert tool["parameters"]["output_path"] == "outputs/ai_video.mp4"


def test_infer_generate_ai_video_extra_keywords():
    from agent import infer_tool_from_message

    for msg in ("做个视频：猫咪在窗台", "制作视频 赛博朋克街道", "生成短片 海浪"):
        tool = infer_tool_from_message(msg)
        assert tool is not None and tool["name"] == "generate_ai_video", msg


def test_infer_slideshow_not_ai_video():
    from agent import infer_tool_from_message

    tool = infer_tool_from_message("用多张图合成视频，图片在桌面")
    assert tool is None or tool["name"] != "generate_ai_video"


def test_infer_deployment_prefers_device_profile():
    from agent import infer_tool_from_message

    tool = infer_tool_from_message("vLLM 启动失败 8001 端口连不上")
    assert tool is not None
    assert tool["name"] == "get_device_profile"


def test_agent_tools_lists_generate_ai_video(client):
    r = client.get("/agent/tools")
    body = r.json()
    assert "generate_ai_video" in body.get("tools", [])
    assert "generate_ai_video" in body.get("groups", {}).get("knowledge_media", [])


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


def test_execute_python_runs_in_workspace():
    fn = TOOL_MAP["execute_python"]
    out = fn({"code": "import pathlib; print(pathlib.Path.cwd().name)"})
    assert "workspace" in out


def test_list_files_desktop_smoke():
    fn = TOOL_MAP["list_files"]
    out = fn({"directory": "~/Desktop"})
    assert "[PATH]" in out or "Not found" in out


def test_read_file_caps_large_file(tmp_path):
    from tools import file_ops

    p = tmp_path / "large.txt"
    p.write_text("x" * 200, encoding="utf-8")
    old_bytes = file_ops.MAX_READ_BYTES
    old_chars = file_ops.READ_PREVIEW_CHARS
    try:
        file_ops.MAX_READ_BYTES = 64
        file_ops.READ_PREVIEW_CHARS = 32
        out = file_ops.read_file(str(p))
    finally:
        file_ops.MAX_READ_BYTES = old_bytes
        file_ops.READ_PREVIEW_CHARS = old_chars
    assert "preview capped" in out.lower()
    assert len(out) < 500


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


def test_http_request_rejects_unsupported_method():
    fn = TOOL_MAP["http_request"]
    out = fn({"url": "http://127.0.0.1:1/health", "method": "TRACE"})
    assert "unsupported method" in out.lower()


def test_web_search_live_optional():
    """Runs when INTEGRATION_NETWORK=1 (e.g. local verify script)."""
    import os

    if os.environ.get("INTEGRATION_NETWORK") != "1":
        pytest.skip("set INTEGRATION_NETWORK=1 to run live search")
    from tools.search import web_search

    out = web_search("Python programming language")
    assert out and len(out) > 20
