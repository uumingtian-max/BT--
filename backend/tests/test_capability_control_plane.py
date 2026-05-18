from capability_registry import list_capabilities, validate_capabilities
from intent_router import route_intent
from tool_registry import all_tool_names


def test_capability_registry_is_valid_against_tool_registry():
    problems = validate_capabilities(set(all_tool_names()))
    assert problems == []
    ids = {item["id"] for item in list_capabilities()}
    assert "system.eye_comfort" in ids
    assert "project.health_check" in ids
    assert "skill.self_evolve" in ids


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


def test_route_unknown_still_returns_safe_plan():
    route = route_intent("嗯")
    assert route["primary_intent"] == "unknown"
    assert route["risk_level"] == "safe"
    assert route["plan"][0]["capability_id"] == "clarify_or_general_chat"
