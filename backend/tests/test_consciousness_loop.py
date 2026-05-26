from __future__ import annotations

import consciousness_loop as cl
import skill_evolution as se
import super_memory as sm


def test_conscious_tick_records_local_reflection(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "DB_PATH", tmp_path / "consciousness.db")
    monkeypatch.setattr(sm, "STORE_DIR", tmp_path / "super")
    monkeypatch.setattr(sm, "STORE_PATH", tmp_path / "super" / "reflections.json")
    monkeypatch.setattr(se, "CANDIDATE_DIR", tmp_path / "candidates")
    monkeypatch.setattr(se, "CANDIDATE_STORE", tmp_path / "candidates" / "candidates.json")

    sm.reflect_on_user_turn("s1", "超级记忆要自成长出候选技能，必须落实。")
    result = cl.run_conscious_tick(phase="manual")
    status = cl.get_consciousness_status()

    assert result["ok"] is True
    assert "TICK/manual" in result["summary"]
    assert status["latest"]["phase"] == "manual"
    assert status["latest"]["signals"]


def test_tick_status_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "DB_PATH", tmp_path / "consciousness.db")
    monkeypatch.setenv("CONSCIOUS_TICK_SEC", "5")

    status = cl.get_consciousness_status()

    assert status["ok"] is True
    assert status["interval_sec"] == 30
