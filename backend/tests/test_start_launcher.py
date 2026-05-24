from __future__ import annotations

import importlib.util
from pathlib import Path

START_PY = Path(__file__).resolve().parents[2] / "start.py"
spec = importlib.util.spec_from_file_location("start", START_PY)
start = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(start)


def test_start_backend_uses_loopback_by_default(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd, cwd=None, env=None, shell=False):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return object()

    monkeypatch.setattr(start, "run", fake_run)
    monkeypatch.setattr(start, "wait_for_port", lambda *args, **kwargs: True)

    start.start_backend()

    cmd = captured["cmd"]
    assert "--host" in cmd
    assert cmd[cmd.index("--host") + 1] == "127.0.0.1"


def test_mode_mobile_binds_all_interfaces(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(start, "check_env", lambda: None)
    monkeypatch.setattr(start, "ok", lambda *_: None)
    monkeypatch.setattr(start, "info", lambda *_: None)
    monkeypatch.setattr(start, "kill_all", lambda: None)
    monkeypatch.setattr(start, "procs", [type("P", (), {"wait": lambda self: None})()])

    def fake_start_backend(*, dev=False, host="127.0.0.1"):
        captured["dev"] = dev
        captured["host"] = host
        return object()

    monkeypatch.setattr(start, "start_backend", fake_start_backend)

    start.mode_mobile()

    assert captured["host"] == "0.0.0.0"
