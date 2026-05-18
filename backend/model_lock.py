"""Model lock plus smart-router entry point."""

from __future__ import annotations

import os


def locked_model_id() -> str:
    if os.environ.get("LOCK_SINGLE_MODEL", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        explicit = os.environ.get("LOCKED_MODEL_ID", "").strip()
        return explicit or _default_model_id()
    return ""


def is_model_locked() -> bool:
    return bool(locked_model_id())


def _default_model_id() -> str:
    try:
        from model_router import get_model

        return get_model("AGENT_DEFAULT_MODEL")
    except Exception:
        return os.environ.get("AGENT_DEFAULT_MODEL", "qwen3.5:4b").strip() or "qwen3.5:4b"


def _looks_like_default_model(model: str | None) -> bool:
    value = (model or "").strip()
    return not value or value == _default_model_id()


def enforce_locked_model(
    model: str | None,
    *,
    user_input: str = "",
    mode: str = "chat",
) -> str:
    locked = locked_model_id()
    if locked:
        return locked

    requested = (model or "").strip()
    if user_input and _looks_like_default_model(requested):
        try:
            from model_router import select_model

            selected, _ = select_model(user_input, mode=mode)
            return selected
        except Exception:
            return _default_model_id()
    return requested or _default_model_id()
