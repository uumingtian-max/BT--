"""Hermes-style extensions: scheduler, gateway, MCP, doctor, session FTS."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_meta_doctor(client: TestClient) -> None:
    r = client.get("/meta/doctor")
    assert r.status_code == 200
    j = r.json()
    assert "checks" in j
    assert isinstance(j["checks"], list)
    assert any(c["name"] == "agent_tools" for c in j["checks"])


def test_meta_tools_registry_is_canonical_probe(client: TestClient) -> None:
    r = client.get("/meta/tools/registry")
    assert r.status_code == 200
    j = r.json()
    assert j.get("ok") is True
    assert isinstance(j.get("tools"), list)
    assert len(j.get("tools") or []) >= 1


def test_habit_pipeline(client: TestClient) -> None:
    r = client.get("/meta/habit")
    assert r.status_code == 200
    j = r.json()
    assert j.get("enabled") is True
    assert isinstance(j.get("check_hours_local"), list)
    assert len(j.get("check_hours_local") or []) >= 1

    r2 = client.post("/meta/habit/run")
    assert r2.status_code == 200
    run = r2.json()
    assert run.get("ok") is True
    assert "doctor" in run
    assert "behavior" in run


def test_scheduler_crud(client: TestClient) -> None:
    r = client.post(
        "/scheduler/jobs",
        json={
            "name": "pytest",
            "message": "say hi",
            "interval_sec": 3600,
            "task_kind": "chat",
            "enabled": False,
        },
    )
    assert r.status_code == 200
    job = r.json()["job"]
    jid = job["id"]
    r2 = client.get("/scheduler/jobs")
    assert any(j["id"] == jid for j in r2.json()["jobs"])
    assert client.delete(f"/scheduler/jobs/{jid}").status_code == 200


def test_gateway_status(client: TestClient) -> None:
    r = client.get("/gateway/status")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_mcp_builtin_call_list_files(client: TestClient) -> None:
    r = client.post(
        "/mcp/call",
        json={
            "server": "builtin",
            "tool": "list_files",
            "arguments": {"directory": "~/Desktop"},
        },
    )
    assert r.status_code == 200
    j = r.json()
    assert j.get("ok") is True
    assert "result" in j


def test_mcp_list_tools(client: TestClient) -> None:
    r = client.get("/mcp/tools")
    assert r.status_code == 200
    j = r.json()
    assert "browser_navigate" in j.get("builtin", [])
    assert "run_parallel_subagents" in j.get("builtin", [])


def test_chat_sessions_search_empty(client: TestClient) -> None:
    r = client.get("/chat/sessions/search", params={"q": ""})
    assert r.status_code == 200
    assert r.json().get("ok") is False


def test_agent_tools_groups(client: TestClient) -> None:
    r = client.get("/agent/tools")
    assert r.status_code == 200
    g = r.json().get("groups", {})
    assert "browser_automation" in g
    assert "parallel" in g


def test_meta_skills_catalog(client: TestClient) -> None:
    r = client.get("/meta/skills")
    assert r.status_code == 200
    j = r.json()
    assert j.get("count", 0) >= 86
    ids = {s["id"] for s in j.get("skills", [])}
    assert "tool_skill_authoring" in ids
    assert "skills_master_index" in ids


def test_operator_dashboard(client: TestClient) -> None:
    r = client.get("/meta/operator-dashboard")
    assert r.status_code == 200
    j = r.json()
    assert j.get("ok") is True
    assert "doctor" in j
    assert "workflow" in j
    assert "agent_tools" in j
    assert isinstance(j.get("failures"), list)


def test_meta_logs(client: TestClient) -> None:
    r = client.get("/meta/logs", params={"lines": 20})
    assert r.status_code == 200
    j = r.json()
    assert j.get("ok") is True
    names = {item["name"] for item in j.get("logs", [])}
    assert "backend.out.log" in names
    assert "backend.err.log" in names


def test_skill_pack_trigger_match() -> None:
    from skill_pack import (
        build_skill_pack_context,
        _load_all_skills,
        _score_skill,
        _message_tokens,
    )

    skills = _load_all_skills()
    text = "帮我上网查一下 python 3.13 发布日期".lower()
    tokens = _message_tokens(text)
    web = next(s for s in skills if s.stem == "tool_web_search")
    assert _score_skill(web, text, tokens) >= 2
    ctx = build_skill_pack_context("帮我上网查一下最新版本")
    assert "tool_web_search" in ctx or "web_search" in ctx
