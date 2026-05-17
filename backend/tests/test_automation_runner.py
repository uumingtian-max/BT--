import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from automation_runner import (
    automation_capabilities,
    normalize_target,
    normalize_task_kind,
)  # noqa: E402


def test_automation_capabilities_are_allow_listed():
    caps = automation_capabilities()
    assert caps["default_task_kind"] == "project_check"
    assert caps["default_target"] == "all"
    assert set(caps["task_kinds"]) == {
        "backend_compile",
        "frontend_build",
        "project_check",
        "repo_health",
    }
    assert set(caps["targets"]) == {"all", "backend", "frontend"}


def test_normalize_task_kind_accepts_known_values():
    assert normalize_task_kind("project_check") == "project_check"
    assert normalize_task_kind(" BACKEND_COMPILE ") == "backend_compile"
    assert normalize_task_kind(None) == "project_check"


def test_normalize_task_kind_rejects_unknown_values():
    try:
        normalize_task_kind("arbitrary_command")
    except ValueError as exc:
        assert "unsupported automation task_kind" in str(exc)
    else:
        raise AssertionError("unknown task kind should be rejected")


def test_normalize_target_accepts_only_known_targets():
    assert normalize_target("all") == "all"
    assert normalize_target(" FRONTEND ") == "frontend"
    assert normalize_target(None) == "all"
    try:
        normalize_target("system")
    except ValueError as exc:
        assert "unsupported automation target" in str(exc)
    else:
        raise AssertionError("unknown target should be rejected")
