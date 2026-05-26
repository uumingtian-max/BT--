from __future__ import annotations

import json
from pathlib import Path

import skill_evolution as se


def test_propose_and_approve_skill_candidate(tmp_path, monkeypatch):
    store = tmp_path / "candidates.json"
    user_skills = tmp_path / "user_skills"
    monkeypatch.setattr(se, "CANDIDATE_DIR", tmp_path)
    monkeypatch.setattr(se, "CANDIDATE_STORE", store)
    monkeypatch.setattr(se, "USER_SKILLS_DIR", user_skills)

    proposed = se.propose_skill_candidate(
        title="真实记忆进化",
        summary="根据用户重复修正生成未知候选技能，先验证再确认激活。",
        evidence=["用户要求真正可以自我根据用户生出未知技能。"],
        trigger_hints=["真实记忆", "自我进化"],
    )

    candidate = proposed["candidate"]
    assert proposed["ok"] is True
    assert candidate["status"] == "pending"
    assert candidate["risk_level"] == "safe"
    assert "真实记忆" in candidate["triggers"]

    approved = se.approve_skill_candidate(candidate["id"])
    skill_path = Path(approved["skill_path"])
    assert skill_path.is_file()
    assert "## 何时使用" in skill_path.read_text(encoding="utf-8")

    stored = json.loads(store.read_text(encoding="utf-8"))
    assert stored[0]["status"] == "approved"


def test_confirm_risk_for_install_or_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(se, "CANDIDATE_DIR", tmp_path)
    monkeypatch.setattr(se, "CANDIDATE_STORE", tmp_path / "candidates.json")

    proposed = se.propose_skill_candidate(
        summary="需要 npm install 后再运行构建，但安装必须等用户确认。",
        evidence=[],
        trigger_hints=["安装确认"],
    )

    assert proposed["candidate"]["risk_level"] == "confirm"
