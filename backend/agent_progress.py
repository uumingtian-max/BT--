"""Thread-safe orchestration progress hook for Agent SSE streaming."""

from __future__ import annotations

from typing import Any, Callable

_on_progress: Callable[[dict[str, Any]], None] | None = None


def set_orchestration_progress(callback: Callable[[dict[str, Any]], None] | None) -> None:
    global _on_progress
    _on_progress = callback


def get_orchestration_progress() -> Callable[[dict[str, Any]], None] | None:
    return _on_progress


def clear_orchestration_progress() -> None:
    global _on_progress
    _on_progress = None
