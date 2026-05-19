"""
Post-task self-evolution: playbook + Critic-Actor feedback loop.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agent_runtime import get_runtime
from llm_client import chat_complete_sync
from memory_store import store_playbook_entry
from workflow_store import list_task_reviews


def ingest_review_lesson(task_message: str, review: dict[str, Any] | None) -> dict[str, Any]:
    rt = get_runtime()
    if not rt.agent_self_evolve or not review:
        return {"ok": False, "reason": "disabled_or_empty"}
    lesson = (review.get("lessons") or "").strip()
    if len(lesson) < 8:
        return {"ok": False, "reason": "short_lesson"}
    snippet = re.sub(r"\s+", " ", (task_message or "").strip())[:120]
    line = f"[自进化复盘] {lesson}（相关任务：{snippet}）"
    row = store_playbook_entry(line, source_session_id="agent", source_role="review", importance=5)
    if not row:
        return {"ok": False, "reason": "store_rejected"}
    return {"ok": True, "stored": row}


def critic_evaluate(
    task_message: str,
    final_output: str,
    *,
    steps_summary: str = "",
) -> dict[str, Any]:
    """Critic scores 1-10; low scores trigger evolution hints."""
    rt = get_runtime()
    if not rt.agent_self_evolve:
        return {"ok": False, "reason": "disabled", "score": 7}
    blob = (
        f"任务：{(task_message or '')[:800]}\n\n"
        f"步骤摘要：{(steps_summary or '')[:1200]}\n\n"
        f"最终输出：{(final_output or '')[:2000]}"
    )
    messages = [
        {
            "role": "system",
            "content": (
                "你是严格 Critic。对 Agent 结果打分 1-10（逻辑、效率、风格、可执行性）。"
                "只输出 JSON：{\"score\":N,\"issues\":[\"...\"],\"fix_hint\":\"...\"}"
            ),
        },
        {"role": "user", "content": blob},
    ]
    try:
        raw = chat_complete_sync(messages, rt.agent_evolve_model, temperature=0.1, http_timeout_sec=45.0)
        m = re.search(r"\{[\s\S]*\}", raw)
        data = json.loads(m.group(0)) if m else {}
        score = int(data.get("score", 7))
        score = max(1, min(10, score))
        return {
            "ok": True,
            "score": score,
            "issues": data.get("issues") or [],
            "fix_hint": str(data.get("fix_hint") or ""),
            "should_retry": score < 6,
        }
    except Exception as exc:
        return {"ok": False, "reason": str(exc), "score": 7, "should_retry": False}


def record_critic_lesson(critic: dict[str, Any], task_message: str) -> dict[str, Any]:
    if not critic.get("ok") or critic.get("score", 10) >= 7:
        return {"ok": False, "reason": "score_ok"}
    hint = (critic.get("fix_hint") or "").strip()
    issues = critic.get("issues") or []
    line = f"[Critic 进化] 分={critic.get('score')} 问题={'; '.join(issues[:3])} 修正={hint}"
    row = store_playbook_entry(line, source_session_id="agent", source_role="critic", importance=5)
    try:
        from vector_memory import get_vector_memory_store, vector_memory_enabled

        if vector_memory_enabled() and row and row.get("id"):
            get_vector_memory_store().add_memory(int(row["id"]), line, category="playbook")
    except Exception:
        pass
    return {"ok": bool(row), "stored": row}


def distill_playbook_with_llm() -> dict[str, Any]:
    """把近期复盘压成少量可执行条写入 playbook；需 AGENT_EVOLVE_LLM=1。"""
    rt = get_runtime()
    if not rt.agent_evolve_llm:
        return {"ok": False, "reason": "AGENT_EVOLVE_LLM not enabled"}
    reviews = list_task_reviews(16)
    if len(reviews) < 3:
        return {"ok": False, "reason": "not_enough_reviews"}
    lines = []
    for r in reviews:
        lines.append(f"- [{r.get('status')}] {r.get('task_type')} | {r.get('lessons', '')}")
    blob = "\n".join(lines)[:6000]
    messages = [
        {
            "role": "system",
            "content": (
                "你是本地 Agent 的元教练。根据下列任务复盘，提炼 3-6 条「以后一律遵守」的短规则。"
                "每条一行，以短横线 - 开头；中文；不要编号；不要解释；不要提模型名。"
            ),
        },
        {"role": "user", "content": blob},
    ]
    raw = chat_complete_sync(messages, rt.agent_evolve_model, temperature=0.15, http_timeout_sec=40.0)
    stored = 0
    for line in raw.splitlines():
        s = line.strip().lstrip("-").strip()
        if len(s) < 12:
            continue
        row = store_playbook_entry(
            f"[自进化蒸馏] {s}",
            source_session_id="agent",
            source_role="llm_distill",
            importance=5,
        )
        if row:
            stored += 1
    return {"ok": True, "stored": stored, "raw_chars": len(raw)}
