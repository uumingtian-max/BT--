"""Pin resident Ollama models; load heavy models on demand only."""

from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Any

import httpx

logger = logging.getLogger("ollama_pins")

# 常驻 VRAM（约 9.7G）：嵌入 + 路由 + 主聊/视觉 + 推理
_DEFAULT_RESIDENT: tuple[str, ...] = (
    "nomic-embed-text:latest",
    "functiongemma:latest",
    "qwen3.5:4b",
    "deepseek-r1:7b",
)

# 按需加载，用完释放（约 8.9G，不占常驻）
_DEFAULT_ON_DEMAND: tuple[str, ...] = ("deepseek-coder-v2:16b",)

MODEL_DEDICATED_ROLES: dict[str, str] = {
    "nomic-embed-text:latest": "向量嵌入（技能/RAG/记忆）· 常驻",
    "functiongemma:latest": "工具路由 / 意图解析 · 常驻",
    "qwen3.5:4b": "答案 / 视觉 / 快答 / 审查 / 结构化 · 常驻",
    "deepseek-r1:7b": "推理 / 规划 / 自进化 · 常驻",
    "deepseek-coder-v2:16b": "复杂写码 / 编排实现 · 按需（用完 unload）",
}

# 仅用于从 .env 收集「常驻」名单（不含 CODE / ORCH_CODER）
_PIN_ENV_KEYS: tuple[str, ...] = (
    "EMBED_MODEL",
    "AGENT_ROUTER_MODEL",
    "FAST_MODEL",
    "TASK_MODEL",
    "OLLAMA_TASK_MODEL",
    "ORCH_SPEECH_MODEL",
    "ORCH_REVIEWER_MODEL",
    "AGENT_DEFAULT_MODEL",
    "ORCH_VISION_MODEL",
    "LOCKED_MODEL_ID",
    "REASONING_MODEL",
    "ORCH_PLANNER_MODEL",
    "AGENT_EVOLVE_MODEL",
)


def keep_alive_duration() -> str:
    """Ollama keep_alive: 5m, 24h, or -1 (forever until server restart)."""
    return os.environ.get("OLLAMA_KEEP_ALIVE", "24h").strip() or "24h"


def strict_model_roles() -> bool:
    return os.environ.get("STRICT_MODEL_ROLES", "1").strip().lower() in ("1", "true", "yes", "on")


def warm_on_startup() -> bool:
    return os.environ.get("OLLAMA_WARM_ON_STARTUP", "1").strip().lower() in ("1", "true", "yes", "on")


def release_on_demand_after_use() -> bool:
    return os.environ.get("OLLAMA_RELEASE_ON_DEMAND", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _parse_csv_models(raw: str, fallback: tuple[str, ...]) -> list[str]:
    if not raw.strip():
        return list(fallback)
    out: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        name = part.strip()
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out


def on_demand_models() -> list[str]:
    return _parse_csv_models(
        os.environ.get("OLLAMA_ON_DEMAND_MODELS", ""),
        _DEFAULT_ON_DEMAND,
    )


def _on_demand_set() -> set[str]:
    return set(on_demand_models())


def resident_models_from_env() -> list[str]:
    """Models to keep warm at startup (excludes on-demand)."""
    explicit = os.environ.get("OLLAMA_RESIDENT_MODELS", "").strip()
    if explicit:
        resident = _parse_csv_models(explicit, _DEFAULT_RESIDENT)
    else:
        seen: set[str] = set()
        resident = []
        od = _on_demand_set()
        for key in _PIN_ENV_KEYS:
            name = os.environ.get(key, "").strip()
            if not name or name in seen or name in od:
                continue
            seen.add(name)
            resident.append(name)
        if not resident:
            resident = list(_DEFAULT_RESIDENT)
    return [m for m in resident if m not in _on_demand_set()]


def pinned_models_from_env() -> list[str]:
    """Alias: resident models only (backward compatible)."""
    return resident_models_from_env()


def is_on_demand_model(model: str) -> bool:
    name = (model or "").strip()
    if not name:
        return False
    if name in _on_demand_set():
        return True
    code = os.environ.get("CODE_MODEL", "").strip() or _DEFAULT_ON_DEMAND[0]
    orch = os.environ.get("ORCH_CODER_MODEL", "").strip() or code
    if name not in {code, orch}:
        return False
    return name not in set(resident_models_from_env())


def _ollama_base() -> str:
    return (os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")


def ollama_chat_body(
    model: str,
    messages: list[dict[str, Any]],
    *,
    stream: bool,
    options: dict[str, Any] | None = None,
    keep_alive: str | int | None = None,
) -> dict[str, Any]:
    ka = keep_alive if keep_alive is not None else keep_alive_duration()
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "keep_alive": ka,
    }
    if options:
        body["options"] = options
    return body


def _warm_chat_model(
    client: httpx.Client,
    base: str,
    model: str,
    *,
    keep_alive: str | int | None = None,
) -> bool:
    try:
        resp = client.post(
            f"{base}/api/chat",
            json=ollama_chat_body(
                model,
                [{"role": "user", "content": "ping"}],
                stream=False,
                options={"temperature": 0},
                keep_alive=keep_alive if keep_alive is not None else keep_alive_duration(),
            ),
            timeout=httpx.Timeout(connect=30.0, read=600.0, write=30.0, pool=10.0),
        )
        if resp.status_code == 404:
            logger.warning("warm skip %s: %s", model, resp.text[:200])
            return False
        resp.raise_for_status()
        logger.info(
            "ollama load (chat): %s keep_alive=%s",
            model,
            keep_alive if keep_alive is not None else keep_alive_duration(),
        )
        return True
    except Exception as exc:
        logger.warning("warm failed %s: %s", model, exc)
        return False


def _warm_embed_model(client: httpx.Client, base: str, model: str) -> bool:
    try:
        payload: dict[str, Any] = {
            "model": model,
            "input": "warm",
            "keep_alive": keep_alive_duration(),
        }
        resp = client.post(
            f"{base}/api/embed",
            json=payload,
            timeout=httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=10.0),
        )
        if resp.status_code == 404:
            resp = client.post(
                f"{base}/api/embeddings",
                json={"model": model, "prompt": "warm", "keep_alive": keep_alive_duration()},
                timeout=httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=10.0),
            )
        resp.raise_for_status()
        logger.info("ollama pinned (embed): %s", model)
        return True
    except Exception as exc:
        logger.warning("warm embed failed %s: %s", model, exc)
        return False


def ensure_on_demand_loaded(model: str) -> bool:
    """Load an on-demand model before a code/orchestration call (does not use 24h pin)."""
    name = (model or "").strip()
    if not name or not is_on_demand_model(name):
        return True
    base = _ollama_base()
    # 短 keep_alive：仅撑住本次任务，最终由 release 卸掉
    session_ka = os.environ.get("OLLAMA_ON_DEMAND_KEEP_ALIVE", "10m").strip() or "10m"
    with httpx.Client() as client:
        embed_name = os.environ.get("EMBED_MODEL", "nomic-embed-text:latest").strip()
        if name == embed_name or "embed" in name.lower():
            return _warm_embed_model(client, base, name)
        return _warm_chat_model(client, base, name, keep_alive=session_ka)


def _model_loaded_in_ps(model: str) -> bool:
    try:
        out = subprocess.check_output(
            ["ollama", "ps"],
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except Exception:
        return False
    base = model.split(":")[0]
    for line in out.splitlines()[1:]:
        if not line.strip():
            continue
        loaded = line.split()[0]
        if loaded == model or loaded.startswith(base + ":"):
            return True
    return False


def release_on_demand_model(model: str) -> bool:
    """Unload on-demand weights (ollama stop + keep_alive=0 fallback)."""
    name = (model or "").strip()
    if not name:
        return False
    try:
        subprocess.run(
            ["ollama", "stop", name],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        time.sleep(1.5)
        if not _model_loaded_in_ps(name):
            logger.info("ollama stop (on-demand): %s", name)
            return True
    except Exception as exc:
        logger.warning("ollama stop failed %s: %s", name, exc)

    base = _ollama_base()
    try:
        with httpx.Client() as client:
            resp = client.post(
                f"{base}/api/generate",
                json={"model": name, "prompt": " ", "stream": False, "keep_alive": 0},
                timeout=httpx.Timeout(connect=15.0, read=60.0, write=15.0, pool=10.0),
            )
            resp.raise_for_status()
            logger.info("ollama unloaded via keep_alive=0: %s", name)
            return True
    except Exception as exc:
        logger.warning("unload failed %s: %s", name, exc)
        return False


def maybe_prepare_ollama_model(model: str) -> bool:
    if is_on_demand_model(model):
        return ensure_on_demand_loaded(model)
    return True


def maybe_release_ollama_model(model: str) -> None:
    if release_on_demand_after_use() and is_on_demand_model(model):
        release_on_demand_model(model)


def warm_all_pinned_models() -> dict[str, Any]:
    """Warm resident models only (on-demand models are skipped)."""
    base = _ollama_base()
    models = resident_models_from_env()
    embed_name = os.environ.get("EMBED_MODEL", "nomic-embed-text:latest").strip()
    ok: list[str] = []
    fail: list[str] = []
    skipped = list(_on_demand_set())
    with httpx.Client() as client:
        for model in models:
            if model == embed_name or "embed" in model.lower():
                if _warm_embed_model(client, base, model):
                    ok.append(model)
                else:
                    fail.append(model)
            else:
                if _warm_chat_model(client, base, model):
                    ok.append(model)
                else:
                    fail.append(model)
    return {
        "ok": True,
        "keep_alive": keep_alive_duration(),
        "strict_roles": strict_model_roles(),
        "resident": models,
        "on_demand": on_demand_models(),
        "skipped_on_demand": skipped,
        "warmed": ok,
        "failed": fail,
    }


def role_map_for_ui() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for model, role in MODEL_DEDICATED_ROLES.items():
        tag = "on_demand" if model in _on_demand_set() or model in _DEFAULT_ON_DEMAND else "resident"
        rows.append({"model": model, "role": role, "pin": tag})
    return rows
