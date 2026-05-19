from capability_executor import execute_capability_request
from capability_registry import list_capabilities, validate_capabilities
from intent_router import route_intent
from specialist_registry import list_specialists, route_specialists, validate_specialists
from tool_registry import all_tool_names


def test_capability_registry_is_valid_against_tool_registry():
    problems = validate_capabilities(set(all_tool_names()))
    assert problems == []
    ids = {item["id"] for item in list_capabilities()}
    assert "system.eye_comfort" in ids
    assert "project.health_check" in ids
    assert "skill.self_evolve" in ids


def test_specialist_registry_references_known_capabilities():
    capability_ids = {item["id"] for item in list_capabilities()}
    problems = validate_specialists(capability_ids)
    assert problems == []
    specialist_ids = {item["id"] for item in list_specialists()}
    assert "operations.sre" in specialist_ids
    assert "testing.reality_checker" in specialist_ids
    assert "memory.habit_coach" in specialist_ids


def test_route_eye_comfort_to_system_capability():
    route = route_intent("屏幕太刺眼了，帮我开个护眼模式")
    assert route["primary_intent"] == "environment_comfort"
    assert route["matches"][0]["capability"]["id"] == "system.eye_comfort"
    assert route["needs_confirmation"] is True
    assert route["plan"][0]["capability_id"] == "system.eye_comfort"


def test_route_project_health_check():
    route = route_intent("检查一下黑光项目，跑一下测试和构建")
    matched_ids = [item["capability"]["id"] for item in route["matches"]]
    assert "project.health_check" in matched_ids
    assert route["confidence"] > 0


def test_route_self_evolution_and_skill_rewrite():
    route = route_intent("根据我的个人使用习惯自动改技能，让黑光自己进化")
    matched_ids = [item["capability"]["id"] for item in route["matches"]]
    assert "skill.self_evolve" in matched_ids
    assert route["risk_level"] in {"confirm", "dangerous"}
    assert any(step["capability_id"] == "skill.self_evolve" for step in route["plan"])


def test_route_specialists_for_agent_architecture_research():
    matches = route_specialists("继续深挖 GitHub 上的 Agent 和 MCP 框架，给黑光落地方案")
    ids = [item["specialist"]["id"] for item in matches]
    assert "research.agent_architect" in ids


def test_route_specialists_for_local_runtime_incident():
    matches = route_specialists("黑光启动不了，检查端口、日志和模型网关")
    ids = [item["specialist"]["id"] for item in matches]
    assert "operations.sre" in ids


def test_capability_executor_dry_run_does_not_execute_real_actions():
    result = execute_capability_request("整理一下桌面", dry_run=True)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["executed"] is False
    assert result["capability_id"] == "files.organize_workspace"
    assert result["plan"]
    assert result["observations"] == []


def test_route_unknown_still_returns_safe_plan():
    route = route_intent("嗯")
    assert route["primary_intent"] == "unknown"
    assert route["risk_level"] == "safe"
    assert route["plan"][0]["capability_id"] == "clarify_or_general_chat"
