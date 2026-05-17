"""
Central runtime settings (OpenHuman-style: one place for models, Ollama URL, context budgets).
Override via environment variables; no extra config file required.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass


def _env_str(key: str, default: str) -> str:
    v = os.environ.get(key, "").strip()
    return v if v else default


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class AgentRuntime:
    llm_backend: str
    ollama_base: str
    openai_base_url: str
    openai_api_key: str
    agent_skill_pack: bool
    agent_self_evolve: bool
    agent_evolve_llm: bool
    agent_evolve_model: str
    default_chat_model: str
    planner_model: str
    coder_model: str
    reviewer_model: str
    vision_model: str
    speech_model: str
    tool_result_max_chars: int
    context_block_max_chars: int
    agent_max_steps: int
    ollama_timeout_sec: float
    chat_history_max_messages: int
    ollama_num_ctx: int
    webhook_url: str

    def ollama_chat_url(self) -> str:
        return self.ollama_base.rstrip("/") + "/api/chat"


_runtime_lock = threading.Lock()
_cached_runtime: AgentRuntime | None = None


def _build_runtime_from_env() -> AgentRuntime:
    base = _env_str("OLLAMA_HOST", "http://127.0.0.1:11434")
    if not base.startswith("http"):
        base = "http://" + base

    raw_backend = _env_str("LLM_BACKEND", "ollama").lower()
    oa_url = _env_str("OPENAI_BASE_URL", "").strip()
    want_openai = raw_backend in ("openai", "openai_compatible", "vllm", "litellm", "localai")
    llm_backend = "openai_compatible" if want_openai and oa_url else "ollama"

    ev_model = _env_str("AGENT_EVOLVE_MODEL", "").strip() or _env_str("AGENT_DEFAULT_MODEL", "qwen3:14b")
    return AgentRuntime(
        llm_backend=llm_backend,
        ollama_base=base,
        openai_base_url=oa_url,
        openai_api_key=_env_str("OPENAI_API_KEY", ""),
        agent_skill_pack=_env_str("AGENT_SKILL_PACK", "1") != "0",
        agent_self_evolve=_env_str("AGENT_SELF_EVOLVE", "1") != "0",
        agent_evolve_llm=_env_str("AGENT_EVOLVE_LLM", "0") == "1",
        agent_evolve_model=ev_model,
        default_chat_model=_env_str("AGENT_DEFAULT_MODEL", "qwen3:14b"),
        planner_model=_env_str("ORCH_PLANNER_MODEL", "qwen3:14b"),
        coder_model=_env_str("ORCH_CODER_MODEL", "qwen3:14b"),
        reviewer_model=_env_str("ORCH_REVIEWER_MODEL", "qwen3:14b"),
        vision_model=_env_str("ORCH_VISION_MODEL", "qwen3:14b"),
        speech_model=_env_str("ORCH_SPEECH_MODEL", "qwen3:14b"),
        tool_result_max_chars=max(800, _env_int("AGENT_TOOL_RESULT_MAX_CHARS", 12000)),
        context_block_max_chars=max(400, _env_int("AGENT_CONTEXT_MAX_CHARS", 6000)),
        agent_max_steps=max(2, min(12, _env_int("AGENT_MAX_STEPS", 6))),
        ollama_timeout_sec=float(max(30, _env_int("OLLAMA_TIMEOUT_SEC", 120))),
        chat_history_max_messages=max(4, min(120, _env_int("CHAT_HISTORY_MAX_MESSAGES", 40))),
        ollama_num_ctx=max(0, min(262144, _env_int("OLLAMA_NUM_CTX", 0))),
        webhook_url=_env_str("WEBHOOK_URL", ""),
    )


def get_runtime() -> AgentRuntime:
    """进程内单例；多 worker 时每个进程独立一份。reload_runtime 会原子替换缓存。"""
    global _cached_runtime
    with _runtime_lock:
        if _cached_runtime is None:
            _cached_runtime = _build_runtime_from_env()
        return _cached_runtime


def reload_runtime() -> AgentRuntime:
    global _cached_runtime
    with _runtime_lock:
        _cached_runtime = _build_runtime_from_env()
        return _cached_runtime


def orchestration_defaults() -> dict[str, str]:
    r = get_runtime()
    return {
        "planner_model": r.planner_model,
        "coder_model": r.coder_model,
        "reviewer_model": r.reviewer_model,
        "vision_model": r.vision_model,
        "speech_model": r.speech_model,
        "llm_backend": r.llm_backend,
    }
