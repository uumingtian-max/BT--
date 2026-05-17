"""
Post-task self-evolution: promote review lessons into durable playbook rows.
Optional LLM batch distillation (expensive) via distill_playbook_with_llm().
"""

from __future__ import annotations

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
