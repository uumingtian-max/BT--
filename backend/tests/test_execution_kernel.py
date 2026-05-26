"""执行内核：#1 第一席 + 默认开启。"""

import execution_kernel as ek
from orchestrator import ModelProfile


def test_kernel_enabled_with_super_on(monkeypatch):
    monkeypatch.setenv("EXECUTION_KERNEL", "1")
    monkeypatch.setenv("BKLT_SUPER_AGENT", "1")
    assert ek.is_execution_kernel_enabled() is True


def test_first_seat_is_architect(monkeypatch):
    monkeypatch.setenv("EXECUTION_KERNEL", "1")
    profile = ModelProfile("p", "c", "r", "v", "s")
    subs = ek.build_kernel_subtasks("做个后端部署", profile, "")
    assert subs[0]["title"].startswith("#1")
    assert subs[0]["kind"] == "expert_architect"
    assert len(subs) <= 4
