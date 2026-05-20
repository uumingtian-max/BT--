"""Agent execution discipline: shell tool and intent inference."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from agent import TOOL_MAP, infer_tool_from_message  # noqa: E402
from agent_intent import extract_shell_command, looks_like_options_only  # noqa: E402
from tools.shell_exec import run_shell  # noqa: E402


def test_run_shell_in_tool_map():
    assert "run_shell" in TOOL_MAP
    assert "execute_capability" in TOOL_MAP


def test_infer_git_status():
    tool = infer_tool_from_message("执行 git status -sb")
    assert tool is not None
    assert tool["name"] == "run_shell"
    assert "git" in tool["parameters"]["command"].lower()


def test_infer_gpu_model():
    tool = infer_tool_from_message("我显卡什么型号的")
    assert tool is not None
    assert tool["name"] == "get_system_info"


def test_infer_perf_optimization():
    tool = infer_tool_from_message("去给我电脑优化一下性能我看看")
    assert tool is not None
    assert tool["name"] == "get_process_list"


def test_infer_gpu_live_status():
    tool = infer_tool_from_message("看看 GPU 显存占用和温度")
    assert tool is not None
    assert tool["name"] == "get_gpu_status"


def test_gpu_status_tool_smoke():
    out = TOOL_MAP["get_gpu_status"]({})
    assert "gpus" in out or "error" in out.lower() or "fallback" in out


def test_process_list_smoke():
    out = TOOL_MAP["get_process_list"]({"top_n": 5, "sort_by": "memory"})
    assert "pid" in out or "MB" in out


def test_network_status_smoke():
    out = TOOL_MAP["get_network_status"]({"port": 8000})
    assert "ok" in out


def test_search_files_smoke():
    out = TOOL_MAP["search_files"]({"directory": "project", "extension": ".py", "max_results": 5})
    assert "results" in out


def test_infer_pytest():
    tool = infer_tool_from_message("跑一下后端测试 pytest")
    assert tool is not None
    assert tool["name"] == "run_shell"
    assert "pytest" in tool["parameters"]["command"]


def test_extract_shell_from_codeblock():
    cmd = extract_shell_command("执行 ```\ngit status -sb\n```")
    assert cmd is not None
    assert "git status" in cmd


def test_run_shell_smoke():
    out = run_shell("echo BT_SHELL_OK", cwd="project")
    assert "BT_SHELL_OK" in out
    assert "exit_code=0" in out


def test_run_shell_via_tool_map():
    out = TOOL_MAP["run_shell"]({"command": "echo via_map", "cwd": "project"})
    assert "via_map" in out


def test_options_only_detection():
    text = "你可以方法一用 git，方法二手动打开。请告诉我你想哪种？"
    assert looks_like_options_only(text)
