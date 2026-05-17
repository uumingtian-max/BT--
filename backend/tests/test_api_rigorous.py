"""
Rigorous API tests: FastAPI TestClient + mocks (no real Ollama required).
Run from repo root: pytest -q
Or: cd backend && pytest tests -q
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client() -> TestClient:
    import main

    return TestClient(main.app)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_telegraf_prometheus_exposition(client: TestClient) -> None:
    r = client.get("/telegraf/prometheus")
    assert r.status_code == 200
    body = r.text
    assert "agent_backend_up" in body
    assert "# TYPE agent_backend_up gauge" in body


def test_telegraf_snapshot_json(client: TestClient) -> None:
    r = client.get("/telegraf/snapshot")
    assert r.status_code == 200
    j = r.json()
    assert j.get("ok") is True
    assert "window_24h" in j
    assert "activity_samples_1h" in j


def test_openapi_contains_new_routes(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    for p in (
        "/meta/models",
        "/meta/info",
        "/meta/alignment",
        "/telegraf/prometheus",
        "/telegraf/snapshot",
        "/notebook/ingest",
        "/notebook/synthesize",
        "/a2a/v1/agent-card",
        "/a2a/v1/message:send",
        "/meta/doctor",
        "/scheduler/jobs",
        "/gateway/status",
        "/mcp/tools",
        "/chat/sessions/search",
    ):
        assert p in paths, f"missing OpenAPI path {p}"


def test_meta_info_shape(client: TestClient) -> None:
    r = client.get("/meta/info")
    assert r.status_code == 200
    j = r.json()
    assert "llm_backend" in j
    assert "defaults" in j and "chat" in j["defaults"]
    assert "hooks" in j and "webhook_configured" in j["hooks"]


def test_meta_alignment_shape(client: TestClient) -> None:
    r = client.get("/meta/alignment")
    assert r.status_code == 200
    j = r.json()
    assert j.get("ok") is True
    assert isinstance(j.get("themes"), list)
    assert any(t.get("id") == "spec_driven" for t in j["themes"])


def test_meta_models_ollama_mock_success(client: TestClient) -> None:
    class FakeResp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"models": [{"model": "mock-model-a"}, {"name": "mock-model-b"}]}

    class FakeCtx:
        def get(self, url: str) -> FakeResp:
            assert "/api/tags" in url
            return FakeResp()

        def __enter__(self) -> FakeCtx:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    with patch("meta_routes.httpx.Client", return_value=FakeCtx()):
        r = client.get("/meta/models")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    ids = {m["id"] for m in j["models"]}
    assert "mock-model-a" in ids
    assert "mock-model-b" in ids


def test_meta_models_ollama_mock_http_error(client: TestClient) -> None:
    class BadResp:
        def raise_for_status(self) -> None:
            raise RuntimeError("connection refused")

    class BadCtx:
        def get(self, url: str) -> BadResp:
            return BadResp()

        def __enter__(self) -> BadCtx:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    import meta_routes

    with meta_routes._OLLAMA_TAGS_CACHE_LOCK:
        meta_routes._OLLAMA_TAGS_CACHE.update(
            {"key": None, "fetched_at": 0.0, "payload": None, "refreshing": False}
        )
    with patch("meta_routes.httpx.Client", return_value=BadCtx()):
        r = client.get("/meta/models")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is False
    assert "error" in j
    assert j["models"] == []


def test_notebook_ingest_validation(client: TestClient) -> None:
    r = client.post("/notebook/ingest", json={"title": "", "text": "x"})
    assert r.status_code == 422


def test_notebook_ingest_ok(client: TestClient) -> None:
    r = client.post("/notebook/ingest", json={"title": "RigorousTest", "text": "corpus line one\ncorpus line two"})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["scope"] == "notebook:RigorousTest"
    assert j["chars"] >= 10


def test_notebook_synthesize_mock_llm(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    import notebook_routes

    async def fake_chat(messages: list, model: str, *, temperature: float = 0.1) -> str:
        assert model
        return "## 合成\n- 要点 A\n- 要点 B\n"

    monkeypatch.setattr(notebook_routes, "chat_complete_async", fake_chat)
    r = client.post(
        "/notebook/synthesize",
        json={"title": "SynthT", "text": "long enough body " * 20},
    )
    assert r.status_code == 200
    j = r.json()
    assert "synthesis" in j and "ingest" in j
    assert "要点" in j["synthesis"]
    assert j["ingest"].get("ok") is True


def test_a2a_agent_card(client: TestClient) -> None:
    r = client.get("/a2a/v1/agent-card")
    assert r.status_code == 200
    j = r.json()
    assert j.get("name") == "local-fastapi-agent"
    assert "default_model" in j


def test_a2a_empty_message(client: TestClient) -> None:
    r = client.post("/a2a/v1/message:send", json={"message": "   "})
    assert r.status_code == 200
    assert r.json()["ok"] is False


def test_a2a_message_mock_run_agent(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    import agent

    async def fake_run(msg: str, model: str):
        assert "hello" in msg
        return [{"type": "final_answer", "content": "mock-final"}]

    monkeypatch.setattr(agent, "run_agent", fake_run)
    r = client.post("/a2a/v1/message:send", json={"text": "hello a2a"})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["final_answer"] == "mock-final"
    assert len(j["steps"]) == 1


def test_chat_preferences_roundtrip(client: TestClient) -> None:
    r = client.post("/chat/preferences", json={"key": "default_model", "value": "pytest-model:x"})
    assert r.status_code == 200
    r2 = client.get("/chat/preferences")
    assert r2.status_code == 200
    prefs = r2.json()
    assert isinstance(prefs, dict)
    assert prefs.get("default_model") == "pytest-model:x"


def test_chat_message_content_is_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    import chat

    monkeypatch.setattr(chat, "CHAT_MESSAGE_MAX_CHARS", 1200)
    capped = chat._cap_message_content("a" * 2000)
    assert len(capped) <= 1300
    assert "chat message truncated" in capped


def test_agent_config_has_webhook_flag(client: TestClient) -> None:
    r = client.get("/agent/config")
    assert r.status_code == 200
    j = r.json()
    assert "llm_backend" in j
    assert "limits" in j


def test_run_agent_webhook_task_runs_with_drain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """create_task(notify...) must complete within the same loop tick + sleep."""
    import agent
    import agent_runtime

    monkeypatch.setenv("WEBHOOK_URL", "http://127.0.0.1:59998/webhook-rigorous")
    agent_runtime.reload_runtime()

    captured: list[dict] = []

    async def rec(payload: dict) -> None:
        captured.append(payload)

    monkeypatch.setattr(agent, "notify_agent_completed", rec)

    long_cn = (
        "根据你的需求，结论如下：这是用于严谨测试的占位模型回复，避免被质量守卫误判为低质量或空话。"
        "第二点说明：当前未连接真实大模型。第三点说明：用于验证 webhook 异步任务是否被调度执行。"
    )

    async def fake_llm(messages: list, model: str, *, temperature: float = 0.1) -> str:
        return long_cn

    monkeypatch.setattr(agent, "call_llm", fake_llm)

    async def go() -> None:
        await agent.run_agent("严谨测试：占位回复与 webhook", "rigorous-dummy")
        await asyncio.sleep(0.25)

    asyncio.run(go())

    assert len(captured) == 1
    assert captured[0].get("event") == "agent_run_done"
    assert "step_count" in captured[0]

    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    agent_runtime.reload_runtime()


def test_orchestrator_router_registered(client: TestClient) -> None:
    """Regression: APIRouter must be imported in orchestrator.py."""
    r = client.get("/openapi.json")
    assert "/agent/orchestrate" in r.json().get("paths", {}) or any(
        "orchestrate" in p for p in r.json().get("paths", {})
    )


def test_agent_run_stream_headers(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """SSE endpoint returns event-stream when mocked run_agent supplies steps."""
    import agent

    async def simple_run(msg: str, model: str):
        return [{"type": "final_answer", "content": "stream-mock"}]

    monkeypatch.setattr(agent, "run_agent", simple_run)
    r = client.post(
        "/agent/run",
        json={"message": "m", "model": "any"},
        headers={"Accept": "text/event-stream"},
    )
    assert r.status_code == 200
    assert "text/event-stream" in (r.headers.get("content-type") or "")
    assert "stream-mock" in r.text


def test_env_bootstrap_setdefault_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mirror env_bootstrap.load_backend_dotenv: existing os.environ wins (setdefault)."""
    import os

    key = "_RIGOROUS_ENVBOOT_LINE__"
    monkeypatch.delenv(key, raising=False)
    os.environ[key] = "already_set"
    line = f"{key}=from_file_value"
    s = line.strip()
    if "=" in s and not s.startswith("#"):
        k, _, val = s.partition("=")
        k, val = k.strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        os.environ.setdefault(k, val)
    assert os.environ[key] == "already_set"

    monkeypatch.delenv(key, raising=False)
    s = line.strip()
    k, _, val = s.partition("=")
    k, val = k.strip(), val.strip()
    os.environ.setdefault(k, val)
    assert os.environ[key] == "from_file_value"


def test_load_backend_dotenv_runs_without_error() -> None:
    import env_bootstrap

    env_bootstrap.load_backend_dotenv()
    env_bootstrap.load_backend_dotenv()


def test_backend_port_default_matches_desktop(monkeypatch: pytest.MonkeyPatch) -> None:
    import env_bootstrap

    monkeypatch.delenv("BACKEND_PORT", raising=False)
    assert env_bootstrap.get_backend_listen_port() == 8000


def test_scheduler_agent_job_uses_run_agent_list(monkeypatch: pytest.MonkeyPatch) -> None:
    import scheduler_runner
    import scheduler_store

    async def fake_run_agent(message: str, model: str):
        assert message == "scheduled"
        return [{"type": "final_answer", "content": "scheduled-ok"}]

    monkeypatch.setattr("agent.run_agent", fake_run_agent)
    monkeypatch.setattr(scheduler_runner, "mark_job_run", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(scheduler_store, "mark_job_run", lambda *_args, **_kwargs: None)

    result = asyncio.run(
        scheduler_runner.run_job_now(
            {
                "id": "pytest-scheduler",
                "task_kind": "agent",
                "message": "scheduled",
                "model": "pytest-model",
                "interval_sec": 3600,
            }
        )
    )
    assert result["ok"] is True
    assert result["text"] == "scheduled-ok"


def test_request_log_middleware_class_importable() -> None:
    from request_log import RequestLogMiddleware, request_log_enabled

    assert callable(RequestLogMiddleware)
    assert request_log_enabled() in (True, False)


def test_safe_output_path_blocks_escape() -> None:
    from safe_paths import OUTPUTS_DIR, safe_output_path

    good = safe_output_path("outputs/pytest-safe/file.txt", default_name="fallback.txt")
    assert good == OUTPUTS_DIR / "pytest-safe" / "file.txt"
    with pytest.raises(ValueError):
        safe_output_path("../outside.txt", default_name="fallback.txt")
