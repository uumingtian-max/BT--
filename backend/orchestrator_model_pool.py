"""Model pool helpers for orchestration.

BKLT should use all suitable local models instead of pinning every orchestration
step to one model.  This module builds role-specific pools and rejects obviously
bad/garbled outputs so the orchestrator can retry with the next model.
"""

from __future__ import annotations

import os
import re
from typing import Callable


def split_models(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[,;\n]+", value) if item.strip()]


def unique_models(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        item = (item or "").strip()
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def env_model_pool(*names: str) -> list[str]:
    models: list[str] = []
    for name in names:
        models.extend(split_models(os.environ.get(name)))
    return unique_models(models)


def looks_garbled_output(text: str) -> bool:
    raw = (text or "").strip()
    if len(raw) < 20:
        return True
    cjk = sum(1 for ch in raw if "\u4e00" <= ch <= "\u9fff")
    alpha = sum(1 for ch in raw if ch.isascii() and ch.isalpha())
    alnum = sum(1 for ch in raw if ch.isalnum())
    punct = sum(1 for ch in raw if not ch.isalnum() and not ch.isspace())
    repeated_de = raw.count("的")
    if repeated_de >= 6 and len(set(raw.replace(" ", ""))) < 18:
        return True
    if alnum < 8 and punct > alnum:
        return True
    if cjk == 0 and alpha < 8 and len(raw) < 120:
        return True
    if re.search(r"(?:/\s*){3,}\d*\s*\w*\s*的\s*的", raw):
        return True
    return False


def pool_for_kind(kind: str, preferred: str, profile, runtime) -> list[str]:
    """Return ordered model candidates for one orchestration role."""
    from ollama_pins import strict_model_roles

    preferred = (preferred or "").strip()
    if strict_model_roles() and preferred:
        return [preferred]

    runtime_fallbacks = unique_models(
        [
            getattr(runtime, "planner_model", ""),
            getattr(runtime, "reviewer_model", ""),
            getattr(runtime, "default_chat_model", ""),
            os.environ.get("REASONING_MODEL", ""),
            os.environ.get("TASK_MODEL", ""),
            os.environ.get("AGENT_DEFAULT_MODEL", ""),
            os.environ.get("FAST_MODEL", ""),
        ]
    )

    if kind in ("planner", "executor", "synthesis"):
        pool = env_model_pool("ORCH_REASONING_MODELS", "ORCH_PLANNER_MODELS")
        pool += [preferred, getattr(profile, "planner_model", ""), os.environ.get("REASONING_MODEL", ""), os.environ.get("TASK_MODEL", "")]
    elif kind == "coder":
        pool = env_model_pool("ORCH_CODER_MODELS", "ORCH_REASONING_MODELS")
        pool += [preferred, getattr(profile, "coder_model", ""), os.environ.get("CODE_MODEL", ""), os.environ.get("REASONING_MODEL", "")]
    elif kind == "reviewer":
        pool = env_model_pool("ORCH_REVIEWER_MODELS", "ORCH_REASONING_MODELS")
        pool += [preferred, getattr(profile, "reviewer_model", ""), os.environ.get("TASK_MODEL", ""), os.environ.get("REASONING_MODEL", "")]
    elif kind == "vision":
        pool = env_model_pool("ORCH_VISION_MODELS")
        pool += [preferred, getattr(profile, "vision_model", ""), os.environ.get("ORCH_VISION_MODEL", ""), os.environ.get("AGENT_DEFAULT_MODEL", "")]
    elif kind == "speech":
        pool = env_model_pool("ORCH_SPEECH_MODELS")
        pool += [preferred, getattr(profile, "speech_model", ""), os.environ.get("ORCH_SPEECH_MODEL", ""), os.environ.get("TASK_MODEL", "")]
    else:
        pool = [preferred]
    return unique_models(pool + runtime_fallbacks)


def call_with_model_pool(
    models: list[str],
    call_once: Callable[[str, str, str], str],
    system_prompt: str,
    user_prompt: str,
    *,
    per_model_retries: int = 1,
) -> tuple[str, int, str]:
    errors: list[str] = []
    attempts = 0
    for model in unique_models(models):
        for _ in range(per_model_retries + 1):
            try:
                output = call_once(model, system_prompt, user_prompt)
                if looks_garbled_output(output):
                    raise RuntimeError(f"garbled model output: {output[:120]}")
                return output, attempts, model
            except Exception as exc:
                errors.append(f"{model}: {exc}")
                attempts += 1
                continue
    raise RuntimeError(" | ".join(errors) if errors else "no orchestration model available")
