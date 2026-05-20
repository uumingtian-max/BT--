"""Regression tests for model_router (23 cases from fixed router)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from model_router import select_model  # noqa: E402


@pytest.fixture(autouse=True)
def _router_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMART_ROUTER_ENABLED", "1")
    monkeypatch.setenv("CODE_MODEL", "code-model")
    monkeypatch.setenv("REASONING_MODEL", "reason-model")
    monkeypatch.setenv("TASK_MODEL", "task-model")
    monkeypatch.setenv("FAST_MODEL", "fast-model")
    monkeypatch.setenv("AGENT_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("AGENT_ROUTER_MODEL", "router-model")


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("你好", "fast"),
        ("hi", "fast"),
        ("谢谢", "fast"),
        ("帮我", "fast"),
        ("写代码", "code"),
        ("解释一下", "reasoning"),
        ("什么是向量数据库", "reasoning"),
        ("帮我找一下架构方案", "reasoning"),
        ("帮我写一份分析报告的代码", "code"),
        ("习惯体检周报", "structured"),
        ("调用工具搜索一下", "agent_route"),
        ("今天聊点别的", "default"),
        ("分析一下", "reasoning"),
        ("debug 这个报错", "code"),
        ("定时任务", "structured"),
        ("在吗", "fast"),
        ("好的", "fast"),
        ("规划方案", "reasoning"),
        ("pip install requests", "code"),
        ("帮我做", "agent_route"),  # _RE_AGENT_ROUTE matches 帮我做
        ("介绍一下 RAG", "reasoning"),
        ("嗯", "fast"),
        ("写个函数", "code"),
    ],
)
def test_select_model_reason(text: str, reason: str) -> None:
    _, got = select_model(text)
    assert got == reason, f"{text!r} → expected {reason}, got {got}"


def test_no_length_based_fast() -> None:
    assert select_model("写代码")[1] != "fast"
    assert select_model("解释一下")[1] != "fast"


def test_architecture_before_agent_route() -> None:
    assert select_model("帮我找一下架构方案")[1] == "reasoning"
