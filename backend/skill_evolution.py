"""Skill evolution candidate store.

This module is intentionally conservative: agents may propose unknown skills
from repeated user behavior, but only an explicit approval promotes them into
active user skills.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skill_pack import invalidate_skill_cache
from skillhub import USER_SKILLS_DIR

ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_DIR = ROOT / "backend" / "skill_candidates"
CANDIDATE_STORE = CANDIDATE_DIR / "candidates.json"

RISK_DANGEROUS = re.compile(r"\b(rm\s+-rf|format\s+[a-z]:|reg\s+delete|delete\s+secrets?)\b", re.I)
RISK_CONFIRM = re.compile(
    r"(pip install|npm install|docker run|Invoke-WebRequest|curl\s+|wget\s+|login|password|token|付款|发布|删除|安装|权限)",
    re.I,
)


@dataclass(frozen=True)
class SkillCandidate:
    id: str
    title: str
    status: str
    triggers: tuple[str, ...]
    rationale: str
    evidence: tuple[str, ...]
    steps: tuple[str, ...]
    validation: tuple[str, ...]
    risk_level: str
    confidence: float
    created_at: int
    updated_at: int
    skill_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "triggers": list(self.triggers),
            "rationale": self.rationale,
            "evidence": list(self.evidence),
            "steps": list(self.steps),
            "validation": list(self.validation),
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "skill_path": self.skill_path,
        }


def ensure_candidate_store() -> None:
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    if not CANDIDATE_STORE.exists():
        CANDIDATE_STORE.write_text("[]\n", encoding="utf-8")


def list_skill_candidates(status: str | None = None) -> list[dict[str, Any]]:
    items = _load_candidates()
    if status:
        items = [item for item in items if item.get("status") == status]
    return sorted(items, key=lambda item: int(item.get("updated_at") or 0), reverse=True)


def propose_skill_candidate(
    *,
    summary: str,
    evidence: list[str] | None = None,
    trigger_hints: list[str] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Create or refresh a pending candidate from observed behavior."""
    cleaned_summary = _clean(summary, limit=1200)
    if not cleaned_summary:
        raise ValueError("summary is required")
    clean_evidence = [_clean(x, limit=500) for x in (evidence or []) if _clean(x, limit=500)]
    triggers = _derive_triggers(cleaned_summary, trigger_hints or [])
    resolved_title = _clean(title or _derive_title(cleaned_summary), limit=80)
    slug = _slug(resolved_title)
    candidate_id = f"skill-{slug}"
    now = int(time.time())
    risk_level = _risk_level("\n".join([cleaned_summary, *clean_evidence, *triggers]))
    candidate = SkillCandidate(
        id=candidate_id,
        title=resolved_title,
        status="pending",
        triggers=tuple(triggers),
        rationale=cleaned_summary,
        evidence=tuple(clean_evidence[:12]),
        steps=tuple(_derive_steps(cleaned_summary)),
        validation=tuple(_derive_validation(cleaned_summary, risk_level)),
        risk_level=risk_level,
        confidence=_confidence(clean_evidence, triggers),
        created_at=now,
        updated_at=now,
        skill_path=None,
    )
    items = _load_candidates()
    existing = next((item for item in items if item.get("id") == candidate_id), None)
    if existing:
        candidate_dict = {**existing, **candidate.to_dict(), "created_at": existing.get("created_at") or now}
        items = [candidate_dict if item.get("id") == candidate_id else item for item in items]
    else:
        items.append(candidate.to_dict())
    _save_candidates(items)
    return {"ok": True, "candidate": candidate.to_dict()}


def approve_skill_candidate(candidate_id: str) -> dict[str, Any]:
    items = _load_candidates()
    item = next((x for x in items if x.get("id") == candidate_id), None)
    if not item:
        raise KeyError(candidate_id)
    if item.get("status") == "approved" and item.get("skill_path"):
        return {"ok": True, "candidate": item, "skill_path": item.get("skill_path")}
    USER_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    filename = _slug(str(item.get("title") or candidate_id)) + ".md"
    path = USER_SKILLS_DIR / filename
    path.write_text(_candidate_to_skill_markdown(item), encoding="utf-8")
    now = int(time.time())
    item["status"] = "approved"
    item["updated_at"] = now
    item["skill_path"] = str(path)
    _save_candidates(items)
    invalidate_skill_cache()
    return {"ok": True, "candidate": item, "skill_path": str(path)}


def reject_skill_candidate(candidate_id: str, reason: str = "") -> dict[str, Any]:
    items = _load_candidates()
    item = next((x for x in items if x.get("id") == candidate_id), None)
    if not item:
        raise KeyError(candidate_id)
    item["status"] = "rejected"
    item["updated_at"] = int(time.time())
    if reason:
        item["reject_reason"] = _clean(reason, limit=500)
    _save_candidates(items)
    return {"ok": True, "candidate": item}


def _load_candidates() -> list[dict[str, Any]]:
    ensure_candidate_store()
    try:
        data = json.loads(CANDIDATE_STORE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _save_candidates(items: list[dict[str, Any]]) -> None:
    ensure_candidate_store()
    CANDIDATE_STORE.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _candidate_to_skill_markdown(item: dict[str, Any]) -> str:
    triggers = ", ".join(str(x) for x in item.get("triggers") or [])
    risk = str(item.get("risk_level") or "safe")
    lines = [
        "---",
        f"name: {_slug(str(item.get('title') or item.get('id') or 'learned-skill'))}",
        f"title: {item.get('title') or '自学习技能'}",
        "source: skill_evolution",
        f"risk_level: {risk}",
        "---",
        "",
        f"# {item.get('title') or '自学习技能'}",
        "",
        f"Triggers: {triggers}",
        "",
        "## 何时使用",
        "",
        str(item.get("rationale") or "").strip(),
        "",
        "## 禁用条件",
        "",
        "- 涉及登录、付款、发布、删除、安装、系统权限或外部下载时，必须先让用户确认。",
        "- 缺少真实验证证据时，只能提出候选方案，不能宣称已完成。",
        "",
        "## 执行步骤",
    ]
    lines.extend(f"- {x}" for x in (item.get("steps") or []))
    lines.extend(["", "## 验证方式"])
    lines.extend(f"- {x}" for x in (item.get("validation") or []))
    lines.extend(["", "## 证据来源"])
    lines.extend(f"- {x}" for x in (item.get("evidence") or []))
    lines.append("")
    return "\n".join(lines)


def _clean(text: str | None, *, limit: int) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())[:limit]


def _derive_title(summary: str) -> str:
    head = re.split(r"[。.!?\n]", summary, maxsplit=1)[0].strip()
    return head[:40] or "自学习候选技能"


def _derive_triggers(summary: str, hints: list[str]) -> list[str]:
    tokens = []
    tokens.extend(_clean(x, limit=32) for x in hints if _clean(x, limit=32))
    tokens.extend(re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,8}", summary))
    stop = {"这个", "那个", "需要", "可以", "真正", "用户", "技能", "记忆", "系统", "项目"}
    out: list[str] = []
    for token in tokens:
        low = token.lower()
        if low in stop or token in stop:
            continue
        if token not in out:
            out.append(token)
        if len(out) >= 12:
            break
    return out or ["自学习", "候选技能"]


def _derive_steps(summary: str) -> list[str]:
    return [
        "先读取当前项目说明、Git 状态和最近运行证据。",
        "从用户目标、重复修正和失败记录里抽取可复用模式。",
        "生成最小可验证补丁或操作计划，不直接扩大权限。",
        "运行与任务匹配的真实验证命令，并记录证据。",
        "把新经验写成候选技能，等待用户确认后再激活。",
    ]


def _derive_validation(summary: str, risk_level: str) -> list[str]:
    checks = ["检查候选技能包含触发条件、禁用条件、执行步骤和验证方式。"]
    if "git" in summary.lower() or "代码" in summary:
        checks.append("运行相关测试或构建，并确认 Git 暂存区不含隐私/生成物。")
    if risk_level != "safe":
        checks.append("确认高风险动作仍需要用户显式批准。")
    return checks


def _risk_level(text: str) -> str:
    if RISK_DANGEROUS.search(text):
        return "dangerous"
    if RISK_CONFIRM.search(text):
        return "confirm"
    return "safe"


def _confidence(evidence: list[str], triggers: list[str]) -> float:
    score = 0.35 + min(len(evidence), 5) * 0.09 + min(len(triggers), 8) * 0.025
    return round(min(score, 0.92), 2)


def _slug(text: str) -> str:
    raw = text.lower().strip()
    raw = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", raw)
    raw = raw.strip("-")
    if not raw:
        raw = "learned-skill"
    return raw[:64]
