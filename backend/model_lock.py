"""单模型锁：仅允许 LOCKED_MODEL_ID / AGENT_DEFAULT_MODEL 指定的 id。"""

from __future__ import annotations

import os


def locked_model_id() -> str:
    explicit = os.environ.get("LOCKED_MODEL_ID", "").strip()
    if explicit:
        return explicit
    if os.environ.get("LOCK_SINGLE_MODEL", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return os.environ.get("AGENT_DEFAULT_MODEL", "qwen3:14b").strip()
    return ""


def is_model_locked() -> bool:
    return bool(locked_model_id())


def enforce_locked_model(model: str | None) -> str:
    locked = locked_model_id()
    if locked:
        return locked
    return (model or "").strip() or os.environ.get("AGENT_DEFAULT_MODEL", "qwen3:14b").strip()
