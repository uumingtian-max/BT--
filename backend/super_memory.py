"""Super memory: tone-aware reflection plus web-learning skill growth."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
STORE_DIR = ROOT / "backend" / "super_memory"
STORE_PATH = STORE_DIR / "reflections.json"

ANGER_MARKERS = ("特么", "tm", "别", "不是", "不对", "自作主张", "你难道", "必须", "落实", "少废话")
URGENCY_MARKERS = ("现在", "马上", "赶紧", "必须", "直接", "立刻", "别停")
TRUST_MARKERS = ("好", "可以", "对", "就这样", "继续")
IMPLEMENT_MARKERS = ("落实", "真实", "真正", "跑", "验证", "git", "合并", "暂存")
MEMORY_MARKERS = ("记忆", "反思", "总结", "优化", "进化", "语气", "偏好", "成长")
SANDBOX_MARKERS = ("沙箱", "sandbox", "computer-use", "权限", "环境")


def reflect_on_user_turn(session_id: str, message: str) -> dict[str, Any]:
    text = _clean(message, 1800)
    if not text:
        return {"ok": False, "reason": "empty"}
    tone = analyze_tone(text)
    reflection = {
        "id": f"refl-{int(time.time())}-{abs(hash(text)) % 100000}",
        "ts": int(time.time()),
        "session_id": _clean(session_id, 120),
        "text_excerpt": text[:500],
        "tone": tone,
        "directives": derive_directives(text, tone),
    }
    items = _load()
    items.append(reflection)
    _save(items[-240:])
    return {"ok": True, "reflection": reflection}


def learn_from_web(query: str, *, goal: str = "") -> dict[str, Any]:
    """Search the web and turn the learning into a pending skill candidate."""
    q = _clean(query, 240)
    if not q:
        return {"ok": False, "reason": "query_required"}
    from skill_evolution import propose_skill_candidate
    from tools.search import web_search

    raw = web_search(q)
    evidence = _extract_evidence(raw)
    summary = (
        f"联网学习主题：{q}。"
        f"目标：{_clean(goal, 300) or '根据外部新方法生成可复用候选技能'}。"
        "把外部结果只当作方向证据，必须重写成本项目自己的步骤和验证方式。"
    )
    candidate = propose_skill_candidate(
        title=f"联网学习：{q[:32]}",
        summary=summary,
        evidence=evidence[:8],
        trigger_hints=["联网学习", "自成长技能", q],
    )
    reflect_on_user_turn(
        "web_learning",
        f"已围绕「{q}」联网学习并生成候选技能；候选必须待用户确认后才激活。",
    )
    return {
        "ok": True,
        "query": q,
        "evidence_count": len(evidence),
        "candidate": candidate.get("candidate"),
        "raw_preview": raw[:1200],
    }


def analyze_tone(text: str) -> dict[str, Any]:
    lower = text.lower()
    angry = _count_markers(lower, ANGER_MARKERS)
    urgent = _count_markers(lower, URGENCY_MARKERS)
    trust = _count_markers(lower, TRUST_MARKERS)
    implement = _count_markers(lower, IMPLEMENT_MARKERS)
    memory = _count_markers(lower, MEMORY_MARKERS)
    sandbox = _count_markers(lower, SANDBOX_MARKERS)
    if angry >= 2:
        mood = "frustrated"
    elif urgent >= 2:
        mood = "urgent"
    elif trust >= 1 and angry == 0:
        mood = "approving"
    else:
        mood = "focused"
    return {
        "mood": mood,
        "anger": angry,
        "urgency": urgent,
        "trust": trust,
        "implementation_pressure": implement,
        "memory_focus": memory,
        "sandbox_focus": sandbox,
    }


def derive_directives(text: str, tone: dict[str, Any]) -> list[str]:
    directives: list[str] = []
    if tone.get("mood") in {"frustrated", "urgent"}:
        directives.append("先承认偏差并修正，不要辩解；直接做可验证改动。")
        directives.append("少写大蓝图，优先给真实文件、接口、测试和当前状态。")
    if tone.get("implementation_pressure", 0) > 0:
        directives.append("用户强调落实时，必须跑命令验证，不能只说规划。")
    if tone.get("memory_focus", 0) > 0:
        directives.append("记忆必须能从用户语气、纠正和重复需求里生成候选反思。")
    if tone.get("sandbox_focus", 0) > 0:
        directives.append("沙箱未完整接入前只能标记 experimental/disabled，不能说成已可用。")
    if "自作主张" in text:
        directives.append("遇到高风险或未完成能力，先降级状态并说明边界。")
    if "联网" in text:
        directives.append("用户允许联网学习时，可搜索外部方向，但只能生成候选技能，不能直接套代码。")
    if "超级记忆" in text:
        directives.append("把超级记忆作为首要任务：语气识别、自我反思、联网学习、候选优化。")
    return _unique(directives) or ["保持简短、真实、可验证；不要过度承诺。"]


def build_super_memory_context(message: str = "") -> str:
    items = _load()
    if not items:
        return ""
    recent = items[-12:]
    current_tone = analyze_tone(message or "")
    directive_counter: dict[str, int] = {}
    for item in recent:
        for directive in item.get("directives") or []:
            directive_counter[str(directive)] = directive_counter.get(str(directive), 0) + 1
    top_directives = sorted(directive_counter.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    lines = [
        "## 超级记忆：语气反思、自我优化、候选技能成长",
        f"- 当前语气判断：{current_tone.get('mood')}；急迫={current_tone.get('urgency')}；不满={current_tone.get('anger')}；落实压力={current_tone.get('implementation_pressure')}",
        "- 运行时反思不等于永久记忆；固化必须走候选技能/用户确认。",
    ]
    if top_directives:
        lines.append("- 本轮必须优先遵守：")
        lines.extend(f"  - {directive}" for directive, _ in top_directives)
    lines.append(f"- 最近一次用户纠正摘要：{recent[-1].get('text_excerpt', '')[:160]}")
    return "\n".join(lines)


def super_memory_status() -> dict[str, Any]:
    items = _load()
    moods: dict[str, int] = {}
    for item in items:
        mood = str((item.get("tone") or {}).get("mood") or "unknown")
        moods[mood] = moods.get(mood, 0) + 1
    return {
        "ok": True,
        "count": len(items),
        "store_path": str(STORE_PATH),
        "moods": moods,
        "latest": items[-5:],
        "context_preview": build_super_memory_context(""),
    }


def _extract_evidence(raw: str) -> list[str]:
    lines = []
    for line in str(raw or "").splitlines():
        clean = _clean(line, 500)
        if len(clean) >= 20:
            lines.append(clean)
        if len(lines) >= 12:
            break
    return lines or [_clean(raw, 500)]


def _load() -> list[dict[str, Any]]:
    if not STORE_PATH.is_file():
        return []
    try:
        data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _save(items: list[dict[str, Any]]) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _count_markers(text: str, markers: tuple[str, ...]) -> int:
    return sum(1 for marker in markers if marker.lower() in text)


def _clean(text: str, limit: int) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())[:limit]


def _unique(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item not in out:
            out.append(item)
    return out
