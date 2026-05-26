from __future__ import annotations

import super_memory as sm


def test_reflect_frustrated_tone_and_context(tmp_path, monkeypatch):
    monkeypatch.setattr(sm, "STORE_DIR", tmp_path)
    monkeypatch.setattr(sm, "STORE_PATH", tmp_path / "reflections.json")

    result = sm.reflect_on_user_turn(
        "s1",
        "超级记忆必须落实，沙箱别特么还在开发就说上线，别自作主张。",
    )

    assert result["ok"] is True
    tone = result["reflection"]["tone"]
    assert tone["mood"] == "frustrated"
    directives = "\n".join(result["reflection"]["directives"])
    assert "沙箱未完整接入前" in directives
    assert "超级记忆" in directives

    ctx = sm.build_super_memory_context("继续落实")
    assert "超级记忆" in ctx
    assert "本轮必须优先遵守" in ctx


def test_learn_from_web_creates_candidate(tmp_path, monkeypatch):
    monkeypatch.setattr(sm, "STORE_DIR", tmp_path / "super")
    monkeypatch.setattr(sm, "STORE_PATH", tmp_path / "super" / "reflections.json")
    monkeypatch.setattr("tools.search.web_search", lambda q: "Result: agent memory skill growth with validation")

    import skill_evolution as se

    monkeypatch.setattr(se, "CANDIDATE_DIR", tmp_path / "candidates")
    monkeypatch.setattr(se, "CANDIDATE_STORE", tmp_path / "candidates" / "candidates.json")

    result = sm.learn_from_web("agent memory skill growth", goal="生成候选技能")

    assert result["ok"] is True
    assert result["candidate"]["status"] == "pending"
    assert "联网学习" in result["candidate"]["title"]
