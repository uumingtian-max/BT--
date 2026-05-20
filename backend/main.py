# pyright: reportMissingImports=false
import env_bootstrap

env_bootstrap.load_backend_dotenv()
env_bootstrap.configure_root_logging()
_LISTEN_PORT = env_bootstrap.get_backend_listen_port()

import asyncio
import os
import secrets
from contextlib import asynccontextmanager
from ipaddress import ip_address, ip_network
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from a2a_bridge import router as a2a_router
from agent import router as agent_router
from automation_routes import router as automation_router
from chat import router as chat_router
from content_routes import router as content_router
from local_agent_api import init_legacy_db, router as local_agent_router
from memory_store import background_memory_maintenance
from meta_routes import router as meta_router
from notebook_routes import router as notebook_router
from observe import (
    background_collector,
    background_pattern_maintenance,
    router as observe_router,
)
from orchestrator import init_orchestrator_db, router as orchestrator_router
from request_log import RequestLogMiddleware, request_log_enabled
from telegraf_routes import router as telegraf_router
from workflow_store import init_workflow_store, router as workflow_router
from scheduler_store import init_scheduler_db
from scheduler_runner import background_scheduler_loop
from habit_pipeline import background_habit_loop, ensure_scheduler_habit_jobs
from scheduler_routes import router as scheduler_router
from gateway_routes import router as gateway_router
from mcp_routes import router as mcp_router
from tool_registry_routes import router as tool_registry_router
from agent_runtime import get_runtime, validate_llm_config
from settings import get_settings, validate_startup_settings


async def warmup_models() -> None:
    """启动时预热默认模型 / Ollama 常驻 pin（失败不阻塞启动）。"""
    import logging

    log = logging.getLogger("main")
    try:
        rt = get_runtime()
        warm = os.environ.get("OLLAMA_WARM_ON_STARTUP", "1").strip().lower() in ("1", "true", "yes", "on")
        if rt.llm_backend == "ollama" and warm:
            from ollama_pins import warm_all_pinned_models

            await asyncio.to_thread(warm_all_pinned_models)
            log.info("Ollama pinned models warmed on startup")
            return
        from llm_client import chat_complete_async

        model = rt.default_chat_model
        await chat_complete_async([{"role": "user", "content": "ping"}], model, temperature=0.0)
        log.info("LLM warmup done: %s", model)
    except Exception as exc:
        log.warning("Model warmup skipped: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    env_bootstrap.configure_root_logging()
    for msg in validate_startup_settings() + validate_llm_config():
        import logging

        logging.getLogger("main").warning("config: %s", msg)
    init_legacy_db()
    init_orchestrator_db()
    init_workflow_store()
    init_scheduler_db()
    try:
        ensure_scheduler_habit_jobs()
    except Exception:
        pass
    try:
        rt = get_runtime()
        if rt.llm_backend == "ollama":
            from meta_routes import _schedule_ollama_tags_refresh

            _schedule_ollama_tags_refresh(rt.ollama_base)
    except Exception:
        pass
    observe_task = asyncio.create_task(background_collector())
    memory_task = asyncio.create_task(background_memory_maintenance())
    pattern_task = asyncio.create_task(background_pattern_maintenance())
    scheduler_task = asyncio.create_task(background_scheduler_loop())
    habit_task = asyncio.create_task(background_habit_loop())
    asyncio.create_task(warmup_models())
    yield
    observe_task.cancel()
    memory_task.cancel()
    pattern_task.cancel()
    scheduler_task.cancel()
    habit_task.cancel()
    try:
        await observe_task
    except asyncio.CancelledError:
        pass
    try:
        await memory_task
    except asyncio.CancelledError:
        pass
    try:
        await pattern_task
    except asyncio.CancelledError:
        pass
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    try:
        await habit_task
    except asyncio.CancelledError:
        pass
    try:
        from llm_client import close_shared_clients

        await close_shared_clients()
    except Exception:
        pass


app = FastAPI(
    title="BT Heiguang Backend",
    version="1.2.0",
    description=(
        "BT（黑光）合并服务：Ollama 或 OpenAI 兼容网关 /chat、工具 Agent /agent/run、编排 /agent/orchestrate；"
        "内容处理 /content/process；行为采样 /observe；Telegraf 可抓取指标 /telegraf/prometheus；"
        "遗留 Local API（POST /agent 任务分解、图像/视频/语音）。"
        "技能包 backend/agent_skills。运行时环境变量见 backend/.env.example。"
    ),
    lifespan=lifespan,
)

_MOBILE_COOKIE = "onyx_mobile_access"
_TAILSCALE_CGNAT = ip_network("100.64.0.0/10")


def _mobile_token() -> str:
    return os.environ.get("MOBILE_ACCESS_TOKEN", "").strip()


def _is_local_or_lan_host(host_header: str) -> bool:
    host = (host_header or "").split(":", 1)[0].strip().lower()
    if host in ("localhost", "127.0.0.1", "::1", "testserver"):
        return True
    try:
        ip = ip_address(host.strip("[]"))
        return ip.is_loopback or ip.is_private or ip.is_link_local or ip in _TAILSCALE_CGNAT
    except ValueError:
        return False


def _lan_requires_token() -> bool:
    s = get_settings()
    host = (s.backend_host or "").strip()
    if host not in ("0.0.0.0", "::"):
        return False
    return s.require_api_token_on_lan


def _mobile_remote_auth_required(request: Request, *, include_auth_routes: bool = False) -> bool:
    token = _mobile_token()
    if not token:
        if _lan_requires_token():
            return not _is_local_or_lan_host(request.headers.get("host", ""))
        return False
    path = request.url.path
    if path == "/health" or (not include_auth_routes and path in ("/mobile-auth/status", "/mobile-auth/login")):
        return False
    if path.startswith(("/mobile", "/static", "/favicon", "/manifest")):
        return False
    return not _is_local_or_lan_host(request.headers.get("host", ""))


def _mobile_request_authenticated(request: Request) -> bool:
    token = _mobile_token()
    if not token:
        return True
    cookie = request.cookies.get(_MOBILE_COOKIE, "")
    bearer = request.headers.get("authorization", "")
    if bearer.lower().startswith("bearer "):
        bearer = bearer[7:].strip()
    return secrets.compare_digest(cookie, token) or secrets.compare_digest(bearer, token)


@app.middleware("http")
async def mobile_remote_access_guard(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    if _mobile_remote_auth_required(request) and not _mobile_request_authenticated(request):
        return JSONResponse(status_code=401, content={"ok": False, "auth_required": True})
    return await call_next(request)


@app.get("/mobile-auth/status")
def mobile_auth_status(request: Request):
    required = _mobile_remote_auth_required(request, include_auth_routes=True)
    return {
        "ok": True,
        "required": required,
        "authenticated": (not required) or _mobile_request_authenticated(request),
    }


@app.post("/mobile-auth/login")
async def mobile_auth_login(request: Request):
    token = _mobile_token()
    data = await request.json()
    submitted = str(data.get("token") or data.get("password") or "").strip()
    if token and secrets.compare_digest(submitted, token):
        resp = JSONResponse({"ok": True})
        resp.set_cookie(
            _MOBILE_COOKIE,
            token,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
        )
        return resp
    return JSONResponse(status_code=401, content={"ok": False, "auth_required": True})


# allow_origins=["*"] + allow_credentials=True 违反 CORS 规范，浏览器会拒绝携带凭证的跨域请求。
# 从环境变量读取允许来源；本机开发默认开放 localhost 常用端口。
# 需远程访问时在 .env 里设置 CORS_ORIGINS=http://your.host:3000（逗号分隔多个）
_cors_raw = os.environ.get("CORS_ORIGINS", "").strip()
_allowed_origins: list[str] = (
    [o.strip() for o in _cors_raw.split(",") if o.strip()]
    if _cors_raw
    else [
        "http://localhost:3000",
        f"http://localhost:{_LISTEN_PORT}",
        "http://127.0.0.1:3000",
        f"http://127.0.0.1:{_LISTEN_PORT}",
    ]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if request_log_enabled():
    app.add_middleware(RequestLogMiddleware)

app.include_router(meta_router, prefix="/meta", tags=["meta"])
app.include_router(tool_registry_router, prefix="/meta", tags=["tools"])
app.include_router(telegraf_router)
app.include_router(notebook_router, prefix="/notebook", tags=["notebook"])
app.include_router(content_router, prefix="/content", tags=["content"])
app.include_router(a2a_router, prefix="/a2a", tags=["a2a"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(agent_router, prefix="/agent", tags=["agent"])
app.include_router(observe_router, prefix="/observe", tags=["observe"])
app.include_router(orchestrator_router, prefix="/agent", tags=["orchestrator"])
app.include_router(workflow_router, tags=["workflow"])
app.include_router(scheduler_router, prefix="/scheduler", tags=["scheduler"])
app.include_router(automation_router, prefix="/automation", tags=["automation"])
app.include_router(gateway_router, prefix="/gateway", tags=["gateway"])
app.include_router(mcp_router, prefix="/mcp", tags=["mcp"])
app.include_router(local_agent_router)

_static = Path(__file__).resolve().parent.parent / "static"
_frontend_build = Path(__file__).resolve().parent.parent / "frontend" / "build"
if _static.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/app",
        StaticFiles(directory=str(_static), html=True),
        name="local_agent_static",
    )

if _frontend_build.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/mobile",
        StaticFiles(directory=str(_frontend_build), html=True),
        name="mobile_frontend",
    )

_outputs = Path(__file__).resolve().parent.parent / "outputs"
_outputs.mkdir(parents=True, exist_ok=True)
from fastapi.staticfiles import StaticFiles

app.mount("/outputs", StaticFiles(directory=str(_outputs)), name="agent_outputs")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    _uv_lvl = (os.environ.get("LOG_LEVEL") or os.environ.get("LOGLEVEL") or "info").strip().lower()
    if _uv_lvl not in ("critical", "error", "warning", "info", "debug", "trace"):
        _uv_lvl = "info"
    _reload_raw = (os.environ.get("UVICORN_RELOAD") or "1").strip().lower()
    _reload = _reload_raw in ("1", "true", "yes", "on")
    _host = (os.environ.get("UVICORN_HOST") or "0.0.0.0").strip() or "0.0.0.0"
    uvicorn.run("main:app", host=_host, port=_LISTEN_PORT, reload=_reload, log_level=_uv_lvl)
