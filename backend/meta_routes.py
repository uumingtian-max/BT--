"""Discovery: models list + small runtime flags for UIs and integrations."""

from __future__ import annotations

import os
import sqlite_wal as sqlite3
import time
import json
import asyncio
from threading import Lock, Thread
from pathlib import Path

import httpx
from fastapi import APIRouter

from agent_runtime import get_runtime
from skill_pack import (
    EMBED_INDEX_PATH,
    EMBED_MODEL,
    _build_embedding_index,
    _load_all_skills,
    _ollama_base_url,
    invalidate_skill_cache,
    list_skills_meta,
)

router = APIRouter()
_OLLAMA_TAGS_CACHE_LOCK = Lock()
_OLLAMA_TAGS_CACHE: dict[str, object] = {
    "key": None,
    "fetched_at": 0.0,
    "payload": None,
    "refreshing": False,
}
_OLLAMA_TAGS_TTL_SEC = 8.0

# OpenAI-compatible /v1/models 缓存（避免 scheduler 每 tick 双次轮询）
_OPENAI_MODELS_CACHE_LOCK = Lock()
_OPENAI_MODELS_CACHE: dict[str, object] = {
    "key": None,
    "fetched_at": 0.0,
    "payload": None,
}
_OPENAI_MODELS_TTL_SEC = 45.0


@router.get("/habit")
def meta_habit_status():
    """每天两次习惯体检流水线状态（见 habit_pipeline）。"""
    from habit_pipeline import get_habit_status

    return get_habit_status()


@router.post("/habit/run")
def meta_habit_run_now():
    """立即执行一次：doctor → 行为分析 → playbook → learned 技能（若模式变化）。"""
    from habit_pipeline import run_habit_check

    return run_habit_check(phase="manual")


def _extra_model_ids() -> list[str]:
    raw = (os.environ.get("EXTRA_MODEL_IDS") or "").strip()
    return [x.strip() for x in raw.split(",") if x.strip()]


def _refresh_ollama_tags(base: str) -> dict[str, object]:
    key = base.rstrip("/")
    with _OLLAMA_TAGS_CACHE_LOCK:
        _OLLAMA_TAGS_CACHE["refreshing"] = True
    try:
        try:
            with httpx.Client(timeout=10.0) as c:
                r = c.get(f"{key}/api/tags")
                r.raise_for_status()
                data = r.json()
            result = {
                "ok": True,
                "models": data.get("models") or [],
                "status_code": 200,
            }
        except Exception as e:
            result = {"ok": False, "error": str(e), "models": []}
        with _OLLAMA_TAGS_CACHE_LOCK:
            _OLLAMA_TAGS_CACHE["key"] = key
            _OLLAMA_TAGS_CACHE["fetched_at"] = time.monotonic()
            _OLLAMA_TAGS_CACHE["payload"] = result
            _OLLAMA_TAGS_CACHE["refreshing"] = False
        return result
    except Exception:
        _OLLAMA_TAGS_CACHE["key"] = key
        _OLLAMA_TAGS_CACHE["fetched_at"] = time.monotonic()
        _OLLAMA_TAGS_CACHE["payload"] = {
            "ok": False,
            "error": "unexpected refresh failure",
            "models": [],
        }
        _OLLAMA_TAGS_CACHE["refreshing"] = False
        raise


def _schedule_ollama_tags_refresh(base: str) -> None:
    key = base.rstrip("/")
    with _OLLAMA_TAGS_CACHE_LOCK:
        if _OLLAMA_TAGS_CACHE.get("refreshing") and _OLLAMA_TAGS_CACHE.get("key") == key:
            return
        _OLLAMA_TAGS_CACHE["key"] = key
        _OLLAMA_TAGS_CACHE["refreshing"] = True

    def _runner() -> None:
        try:
            _refresh_ollama_tags(key)
        except Exception:
            with _OLLAMA_TAGS_CACHE_LOCK:
                _OLLAMA_TAGS_CACHE["refreshing"] = False

    Thread(target=_runner, daemon=True).start()


def _get_ollama_tags(base: str, *, allow_background: bool = False) -> dict[str, object]:
    key = base.rstrip("/")
    now = time.monotonic()
    cached_key = _OLLAMA_TAGS_CACHE.get("key")
    fetched_at = float(_OLLAMA_TAGS_CACHE.get("fetched_at") or 0.0)
    payload = _OLLAMA_TAGS_CACHE.get("payload")
    refreshing = bool(_OLLAMA_TAGS_CACHE.get("refreshing"))
    if cached_key == key and payload is not None:
        if (now - fetched_at) <= _OLLAMA_TAGS_TTL_SEC:
            return (
                payload if isinstance(payload, dict) else {"ok": False, "error": "invalid cache payload", "models": []}
            )
        if allow_background:
            _schedule_ollama_tags_refresh(key)
            if isinstance(payload, dict):
                return {**payload, "stale": True}
        else:
            return _refresh_ollama_tags(key)
    if allow_background:
        if not refreshing or cached_key != key:
            _schedule_ollama_tags_refresh(key)
        return {"ok": None, "warming": True, "models": []}
    return _refresh_ollama_tags(key)


def _fetch_openai_compatible_models(base_url: str) -> list[dict[str, str]]:
    """从 vLLM / LiteLLM 等 OpenAI 兼容网关读取 /v1/models（带 TTL 缓存，避免双次轮询）。"""
    base = (base_url or "").strip().rstrip("/")
    if not base:
        return []
    now = time.monotonic()
    with _OPENAI_MODELS_CACHE_LOCK:
        if (
            _OPENAI_MODELS_CACHE.get("key") == base
            and (now - float(_OPENAI_MODELS_CACHE.get("fetched_at") or 0)) < _OPENAI_MODELS_TTL_SEC
        ):
            return list(_OPENAI_MODELS_CACHE.get("payload") or [])
    url = base if base.endswith("/v1") else f"{base}/v1"
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(f"{url}/models")
            r.raise_for_status()
            data = r.json()
        out: list[dict[str, str]] = []
        for item in data.get("data") or []:
            mid = item.get("id") if isinstance(item, dict) else None
            if mid:
                out.append({"id": str(mid), "source": "openai_compatible"})
    except Exception:
        out = []
    with _OPENAI_MODELS_CACHE_LOCK:
        _OPENAI_MODELS_CACHE["key"] = base
        _OPENAI_MODELS_CACHE["fetched_at"] = time.monotonic()
        _OPENAI_MODELS_CACHE["payload"] = out
    return out


def _runtime_model_entries(rt) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for mid in (
        rt.default_chat_model,
        getattr(rt, "fast_model", ""),
        getattr(rt, "router_model", ""),
        getattr(rt, "embed_model", ""),
        getattr(rt, "reasoning_model", ""),
        getattr(rt, "code_model", ""),
        getattr(rt, "task_model", ""),
        rt.planner_model,
        rt.coder_model,
        rt.reviewer_model,
        rt.vision_model,
        rt.speech_model,
    ):
        m = (mid or "").strip()
        if m and m not in seen:
            seen.add(m)
            out.append({"id": m, "source": "runtime"})
    return out


def _list_models_payload(*, strict_probe: bool = True) -> dict[str, object]:
    from model_lock import is_model_locked, locked_model_id

    if is_model_locked():
        mid = locked_model_id()
        return {"ok": True, "models": [{"id": mid, "source": "locked"}], "locked": True}
    rt = get_runtime()
    out: list[dict[str, str]] = []
    warming = False
    stale = False
    if rt.llm_backend == "ollama":
        payload = _get_ollama_tags(rt.ollama_base, allow_background=not strict_probe)
        if payload.get("ok"):
            for m in payload.get("models") or []:
                name = m.get("model") or m.get("name")
                if name:
                    out.append({"id": str(name), "source": "ollama"})
            stale = bool(payload.get("stale"))
        elif strict_probe:
            return {
                "ok": False,
                "error": payload.get("error", "unknown error"),
                "models": [],
            }
        else:
            warming = bool(payload.get("warming"))
            out.extend(_runtime_model_entries(rt))
    else:
        remote = _fetch_openai_compatible_models(rt.openai_base_url)
        if remote:
            out.extend(remote)
        else:
            out.extend(_runtime_model_entries(rt))
    for x in _extra_model_ids():
        out.append({"id": x, "source": "extra"})
    data: dict[str, object] = {"ok": True, "models": out}
    if warming:
        data["warming"] = True
    if stale:
        data["stale"] = True
    return data


def _meta_doctor_payload(*, strict_probe: bool = True) -> dict[str, object]:
    """Hermes-style health check: Ollama, DBs, feature flags, optional modules."""
    import sqlite3
    from pathlib import Path

    rt = get_runtime()
    backend = Path(__file__).resolve().parent
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = "", *, optional: bool = False) -> None:
        if optional and not ok:
            checks.append(
                {
                    "name": name,
                    "status": "skip",
                    "detail": detail or "optional (not configured)",
                }
            )
        else:
            checks.append({"name": name, "status": "ok" if ok else "fail", "detail": detail})

    add("llm_backend", True, rt.llm_backend)
    try:
        from model_router import routing_info

        info = routing_info("帮我写个 Python 脚本", mode="chat")
        add(
            "smart_router",
            bool(info.get("smart_router_enabled")),
            f"{info.get('reason')} -> {info.get('model')}",
        )
    except Exception as e:
        add("smart_router", False, str(e), optional=True)
    if rt.llm_backend == "ollama":
        payload = _get_ollama_tags(rt.ollama_base, allow_background=not strict_probe)
        if payload.get("ok"):
            add(
                "ollama_reachable",
                True,
                f"{rt.ollama_base.rstrip('/')} HTTP {payload.get('status_code', 200)}",
            )
        elif payload.get("warming") and not strict_probe:
            add(
                "ollama_reachable",
                False,
                "warming up; probe running in background",
                optional=True,
            )
        else:
            add("ollama_reachable", False, str(payload.get("error", "unknown error")))
    else:
        url_set = bool((rt.openai_base_url or "").strip())
        add("openai_base_url", url_set, rt.openai_base_url or "(empty)")
        if url_set:
            remote = _fetch_openai_compatible_models(rt.openai_base_url)
            gw_ok = bool(remote)
            detail = (
                f"{len(remote)} model(s) from /v1/models"
                if gw_ok
                else "网关不可达或未返回模型；Windows 原生上 vLLM 常不可用，建议改 LLM_BACKEND=ollama（Ollama 直连 GPU）或单独 Linux/WSL GPU 机上跑网关"
            )
            add("openai_compatible_gateway", gw_ok, detail)

    for db_name in (
        "memory.db",
        "chat.db",
        "workflow.db",
        "behavior.db",
        "scheduler.db",
        "orchestrator.db",
    ):
        p = backend / db_name
        add(f"db:{db_name}", p.is_file(), str(p))

    webhook_url = (rt.webhook_url or "").strip()
    webhook_required = os.environ.get("WEBHOOK_REQUIRED", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if webhook_url:
        add("webhook", True, "configured")
    elif webhook_required:
        add("webhook", False, "WEBHOOK_URL empty but WEBHOOK_REQUIRED=1")
    else:
        add("webhook", False, "optional (not configured)", optional=True)
    add(
        "scheduler",
        os.environ.get("SCHEDULER_ENABLED", "1") not in ("0", "false", "off"),
    )
    add("gateway", os.environ.get("GATEWAY_ENABLED", "1") not in ("0", "false", "off"))
    add(
        "mcp_bridge",
        os.environ.get("MCP_BRIDGE_ENABLED", "1") not in ("0", "false", "off"),
    )

    try:
        import playwright  # noqa: F401

        add("playwright", True, "installed")
    except ImportError:
        # 浏览器自动化非对话核心；未安装不应把整页打成「后端告警」
        add(
            "playwright",
            False,
            "pip install playwright && playwright install chromium",
            optional=True,
        )

    pw_root = (os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or "").strip()
    if not pw_root:
        pw_root = str(Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright")
    chromium = list(Path(pw_root).glob("chromium-*")) if pw_root and Path(pw_root).is_dir() else []
    add("playwright_chromium", bool(chromium), pw_root or "(default)", optional=True)

    from media_fallback import local_sd_enabled, placeholder_enabled

    if local_sd_enabled():
        add("local_sd", True, "ENABLE_LOCAL_SD=1")
    else:
        add(
            "local_sd",
            False,
            "optional: ENABLE_LOCAL_SD=1 + requirements-media.txt",
            optional=True,
        )
    add("image_placeholder", placeholder_enabled(), "ENABLE_IMAGE_PLACEHOLDER")

    try:
        from ddgs import DDGS  # noqa: F401

        add("ddgs_search", True, "installed")
    except ImportError:
        add("ddgs_search", False, "pip install ddgs", optional=True)

    try:
        from chat import DB_PATH as _chat_db_path

        conn = sqlite3.connect(_chat_db_path)
        conn.execute("SELECT 1 FROM messages_fts LIMIT 1")
        conn.close()
        add("chat_fts", True, "messages_fts on chat.db ready")
    except Exception as e:
        add("chat_fts", False, str(e), optional=True)

    from agent import TOOL_MAP

    add("agent_tools", len(TOOL_MAP) >= 20, f"{len(TOOL_MAP)} tools registered")

    try:
        from embed_backend import embed_status

        strict_embed = os.environ.get("EMBED_DOCTOR_PROBE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        est = embed_status(probe=strict_embed)
        backend = str(est.get("backend") or "ollama")
        if backend in ("openvino", "ov", "npu"):
            ok = bool(est.get("openvino_ok"))
            if est.get("openvino_probe") == "skipped":
                detail = f"dir ok ({est.get('ov_dir')}); set EMBED_DOCTOR_PROBE=1 to compile NPU"
            elif ok:
                detail = f"device={est.get('openvino_device')} dim={est.get('dim')}"
            else:
                detail = str(est.get("openvino_error", "openvino probe failed"))
            add("embed_npu", ok, detail)
        else:
            add(
                "embed_backend",
                True,
                f"ollama @ {est.get('ollama_base')} model={est.get('ollama_model')}",
            )
    except Exception as e:
        add("embed_backend", False, str(e), optional=True)

    failed = [c for c in checks if c["status"] == "fail"]
    return {
        "ok": len(failed) == 0,
        "failed_count": len(failed),
        "checks": checks,
    }


@router.get("/skills")
def meta_skills():
    """可发现技能包：backend/agent_skills/*.md（对标 claude-skills 目录，不克隆外仓）。"""
    rt = get_runtime()
    items = list_skills_meta()
    return {
        "ok": True,
        "enabled": rt.agent_skill_pack,
        "dir": "backend/agent_skills",
        "count": len(items),
        "embedding_router": _skill_embedding_status(),
        "skills": items,
    }


@router.post("/skills/reload")
def meta_skills_reload():
    """显式清空技能缓存并返回最新列表。"""
    invalidate_skill_cache()
    return meta_skills()


def _skill_embedding_status() -> dict[str, object]:
    status: dict[str, object] = {
        "enabled": True,
        "model": EMBED_MODEL,
        "ollama_base": _ollama_base_url(),
        "index_path": str(EMBED_INDEX_PATH),
        "index_exists": EMBED_INDEX_PATH.is_file(),
        "vectors": 0,
    }
    if EMBED_INDEX_PATH.is_file():
        try:
            data = json.loads(EMBED_INDEX_PATH.read_text(encoding="utf-8"))
            vectors = data.get("vectors") if isinstance(data, dict) else {}
            status["vectors"] = len(vectors) if isinstance(vectors, dict) else 0
            status["created_at"] = data.get("created_at") if isinstance(data, dict) else None
        except (OSError, json.JSONDecodeError):
            status["index_error"] = "unreadable index"
    return status


@router.get("/skills/embedding")
def meta_skills_embedding_status():
    return {"ok": True, **_skill_embedding_status()}


@router.post("/skills/embedding/rebuild")
async def meta_skills_embedding_rebuild():
    skills = _load_all_skills()
    try:
        index = await asyncio.to_thread(_build_embedding_index, skills)
    except Exception as e:
        return {"ok": False, **_skill_embedding_status(), "error": str(e)}
    return {
        "ok": True,
        "model": index.get("model"),
        "ollama_base": index.get("ollama_base"),
        "vectors": len(index.get("vectors", {})),
        "index_path": str(EMBED_INDEX_PATH),
    }


@router.get("/models")
def list_models():
    return _list_models_payload(strict_probe=True)


@router.get("/info")
def meta_info():
    r = get_runtime()
    return {
        "llm_backend": r.llm_backend,
        "ollama_base": r.ollama_base,
        "openai_base_url_set": bool((r.openai_base_url or "").strip()),
        "defaults": {"chat": r.default_chat_model},
        "smart_router": {
            "enabled": getattr(r, "smart_router_enabled", False),
            "models": {
                "fast": getattr(r, "fast_model", ""),
                "agent_router": getattr(r, "router_model", ""),
                "embed": getattr(r, "embed_model", ""),
                "reasoning": getattr(r, "reasoning_model", ""),
                "code": getattr(r, "code_model", ""),
                "task": getattr(r, "task_model", ""),
            },
        },
        "hooks": {"webhook_configured": bool((r.webhook_url or "").strip())},
        "extensions": {
            "scheduler": os.environ.get("SCHEDULER_ENABLED", "1") not in ("0", "false", "off"),
            "gateway": os.environ.get("GATEWAY_ENABLED", "1") not in ("0", "false", "off"),
            "mcp_bridge": os.environ.get("MCP_BRIDGE_ENABLED", "1") not in ("0", "false", "off"),
            "chat_fts": True,
        },
    }


@router.get("/alignment")
def community_alignment():
    """Curated map: trending *themes* ↔ local features (no live GitHub scraping)."""
    return {
        "ok": True,
        "snapshot_date": "2026-05-15",
        "themes": [
            {
                "id": "spec_driven",
                "label": "Spec-driven delivery",
                "repos_public": ["github/spec-kit"],
                "local": [
                    "agent_skills/spec_minimal_steps.md",
                    "chat + agent system prompts",
                ],
            },
            {
                "id": "agent_skills",
                "label": "Discoverable agent skills",
                "repos_public": [
                    "obra/superpowers",
                    "mattpocock/skills",
                    "K-Dense-AI/scientific-agent-skills",
                    "alirezarezvani/claude-skills",
                ],
                "local": [
                    "backend/agent_skills/*.md (83+ playbooks)",
                    "GET /meta/skills",
                    "agent_skills/skills_master_index.md",
                    "agent_skills/claude_skills_domain_map.md",
                    "skill_pack.build_skill_pack_context",
                ],
            },
            {
                "id": "tool_playbooks",
                "label": "Per-tool agent playbooks",
                "repos_public": ["Anthropic tool-use patterns"],
                "local": ["agent_skills/tool_*.md", "GET /agent/tools"],
            },
            {
                "id": "feature_api_playbooks",
                "label": "Feature API playbooks (memory, scheduler, gateway)",
                "repos_public": ["managed agent platforms"],
                "local": [
                    "agent_skills/feature_*.md",
                    "/chat/memories/*",
                    "/scheduler/*",
                    "/gateway/*",
                ],
            },
            {
                "id": "persistent_memory",
                "label": "Persistent memory & eval mindset",
                "repos_public": ["rohitg00/agentmemory"],
                "local": ["memory_store", "/chat/memories/*"],
            },
            {
                "id": "personal_local_ai",
                "label": "Private local super-agent stack",
                "repos_public": ["tinyhumansai/openhuman"],
                "local": [
                    "/agent/run",
                    "/agent/orchestrate",
                    "OLLAMA_HOST / LLM_BACKEND",
                ],
            },
            {
                "id": "metrics_observability",
                "label": "Metrics & observability",
                "repos_public": ["influxdata/telegraf"],
                "local": ["/telegraf/prometheus", "/telegraf/snapshot"],
            },
            {
                "id": "trending_devs_202605",
                "label": "GitHub Trending Developers (May 2026)",
                "repos_public": [
                    "alirezarezvani/claude-skills",
                    "ruvnet/ruflo",
                    "garrytan/gstack",
                    "backnotprop/plannotator",
                    "holtskinner/A2AWalkthrough",
                ],
                "local": [
                    "agent_skills/github_trending_developers.md",
                    "GET /meta/skills",
                    "GET /meta/alignment",
                ],
            },
            {
                "id": "a2a_interop",
                "label": "Agent2Agent interop",
                "repos_public": ["holtskinner/A2AWalkthrough"],
                "local": [
                    "/a2a/v1/agent-card",
                    "/a2a/v1/message:send",
                    "agent_skills/a2a_interop_lite.md",
                ],
            },
            {
                "id": "plan_review",
                "label": "Plan & diff review before execution",
                "repos_public": ["backnotprop/plannotator"],
                "local": ["agent_skills/agent_plan_diff_review.md", "/agent/run"],
            },
            {
                "id": "recursive_long_doc",
                "label": "Recursive long-document reasoning",
                "repos_public": ["zircote/rlm-rs"],
                "local": [
                    "agent_skills/recursive_long_document.md",
                    "run_parallel_subagents",
                ],
            },
        ],
        "notes": [
            "Themes are inspirational only; this API does not clone or call third-party repos.",
            "Curated vendor clones (reference only): agency-agents, gstack — see vendor/repos.manifest.json and skill bt_external_repos.",
            "For GitHub Trending Developers ask Agent: 热榜 / trending developers / github trending — loads github_trending_developers + weekly_trend_map.",
            "Full skill list: GET /meta/skills",
        ],
    }


@router.get("/doctor")
def meta_doctor():
    return _meta_doctor_payload(strict_probe=True)


def _tail_lines(path: Path, limit: int = 60) -> list[str]:
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    lines = [line.rstrip("\r") for line in text.splitlines()]
    if limit <= 0:
        return lines
    return lines[-limit:]


@router.get("/logs")
def meta_logs(lines: int = 60):
    root = Path(__file__).resolve().parent.parent
    logs_dir = root / "logs"
    limit = max(10, min(400, int(lines)))
    items = []
    for name in ("backend.out.log", "backend.err.log"):
        path = logs_dir / name
        items.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.is_file(),
                "size": path.stat().st_size if path.is_file() else 0,
                "updated_at": int(path.stat().st_mtime) if path.is_file() else None,
                "lines": _tail_lines(path, limit),
            }
        )
    return {"ok": True, "logs": items, "line_limit": limit}


@router.get("/operator-dashboard")
def operator_dashboard():
    from agent import TOOL_MAP
    from chat import DB_PATH as CHAT_DB_PATH
    from habit_pipeline import get_habit_status
    from memory_store import get_memory_dashboard
    from observe import observe_status
    from workflow_store import get_workflow_dashboard

    doctor = _meta_doctor_payload(strict_probe=False)
    models = _list_models_payload(strict_probe=False)
    habit = get_habit_status()
    workflow = get_workflow_dashboard()
    memory = get_memory_dashboard()
    observe = observe_status()

    chat_summary = {"session_count": 0, "recent_sessions": []}
    try:
        conn = sqlite3.connect(CHAT_DB_PATH)
        chat_summary["session_count"] = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        rows = conn.execute(
            "SELECT id, COALESCE(title, ''), created_at FROM sessions ORDER BY created_at DESC LIMIT 8"
        ).fetchall()
        conn.close()
        chat_summary["recent_sessions"] = [{"id": row[0], "title": row[1], "created_at": row[2]} for row in rows]
    except Exception as e:
        chat_summary["error"] = str(e)

    failures = []
    for check in doctor.get("checks", []):
        if check.get("status") == "fail":
            failures.append(
                {
                    "source": "doctor",
                    "name": check.get("name"),
                    "detail": check.get("detail", ""),
                }
            )
    for item in workflow.get("recent_reviews", [])[:12]:
        if item.get("status") == "failed":
            failures.append(
                {
                    "source": "workflow",
                    "name": item.get("tool_name") or item.get("task_type") or "task",
                    "detail": item.get("task_text", "")[:180],
                }
            )

    return {
        "ok": True,
        "generated_at": int(time.time()),
        "doctor": doctor,
        "models": models,
        "habit": habit,
        "workflow": workflow,
        "memory": {
            "memory_count": memory.get("memory_count", 0),
            "knowledge_tree": memory.get("knowledge_tree", {}),
            "vault_dir": memory.get("vault_dir", ""),
        },
        "observe": observe,
        "chat": chat_summary,
        "agent_tools": {"count": len(TOOL_MAP)},
        "failures": failures[:20],
    }


@router.get("/visual-events")
def meta_visual_events(limit: int = 80, source: str | None = None, run_id: str | None = None):
    """Neural topology / workbench: recent agent & automation pulses."""
    from visual_event_bus import list_events

    return {"ok": True, "events": list_events(limit=limit, source=source, run_id=run_id)}


@router.get("/run-graph/runs")
def meta_run_graph_list(limit: int = 50, source: str | None = None):
    from run_graph_store import list_runs as graph_list_runs

    return {"ok": True, "runs": graph_list_runs(limit=limit, source=source)}


@router.get("/run-graph/runs/{run_id}")
def meta_run_graph_detail(run_id: str):
    from run_graph_store import get_run_detail

    detail = get_run_detail(run_id)
    if not detail:
        return {"ok": False, "error": "run not found"}
    return {"ok": True, "run": detail}
