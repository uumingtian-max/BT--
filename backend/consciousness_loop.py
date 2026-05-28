"""Low-risk TICK loop for BT's "always alive" consciousness layer.

Inspired by continuous-agent loops, but implemented as a local, auditable,
non-tool-running background process. It never uploads, installs, deletes, or
executes user actions; it only records pulses, reflects on local state, and can
propose pending skills through the existing candidate gate.
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite_wal as sqlite3
import time
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "consciousness.db"


def tick_enabled() -> bool:
    return os.environ.get("CONSCIOUS_TICK_ENABLED", "1").strip().lower() not in (
        "0",
        "false",
        "off",
        "no",
    )


def tick_interval_sec() -> int:
    return max(30, int(os.environ.get("CONSCIOUS_TICK_SEC", "180") or "180"))


def init_consciousness_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS consciousness_ticks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            phase TEXT NOT NULL,
            summary TEXT NOT NULL,
            signals_json TEXT NOT NULL DEFAULT '[]',
            proposed_skill_id TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_consciousness_ticks_ts ON consciousness_ticks(ts)")
    conn.commit()
    conn.close()


init_consciousness_db()


_tick_running = False


def tick_loop_running() -> bool:
    return _tick_running or tick_enabled()


def run_conscious_tick(*, phase: str = "manual") -> dict[str, Any]:
    """Run one local reflection pulse."""
    init_consciousness_db()
    signals = _collect_signals()
    summary = _build_summary(signals, phase=phase)
    insight = ""
    try:
        insight = _run_tick_llm_insight_sync()
        if insight:
            summary = f"{summary} | 洞察: {insight[:120]}"
    except Exception as exc:
        signals.append(f"tick_llm_failed: {exc}")
    try:
        from super_memory import reflect_and_update

        reflect_and_update()
    except Exception as exc:
        signals.append(f"reflect_failed: {exc}")
    proposed_skill_id = ""

    if _should_propose_skill(signals):
        try:
            from skill_evolution import propose_skill_candidate

            proposed = propose_skill_candidate(
                title="意识循环自省优化",
                summary="TICK 循环发现用户近期持续强调真实落实、超级记忆和候选技能成长；生成一个待确认技能用于后续固化。",
                evidence=signals[:8],
                trigger_hints=["TICK", "意识循环", "超级记忆", "候选技能"],
            )
            proposed_skill_id = str((proposed.get("candidate") or {}).get("id") or "")
        except Exception as exc:
            signals.append(f"skill_proposal_failed: {exc}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO consciousness_ticks (ts, phase, summary, signals_json, proposed_skill_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (int(time.time()), phase, summary, json.dumps(signals, ensure_ascii=False), proposed_skill_id),
    )
    conn.execute(
        "DELETE FROM consciousness_ticks WHERE ts < ?",
        (int(time.time()) - 14 * 86400,),
    )
    conn.commit()
    conn.close()
    return {
        "ok": True,
        "phase": phase,
        "summary": summary,
        "insight": insight,
        "signals": signals,
        "proposed_skill_id": proposed_skill_id,
    }


def _run_tick_llm_insight_sync() -> str:
    import asyncio

    return asyncio.run(_tick_llm_insight_async())


async def _tick_llm_insight_async() -> str:
    from llm_dual_route import llm_quick_call
    from memory_store import list_memories, store_memory

    recent = list_memories(20)
    if not recent:
        return ""
    blob = "; ".join(str(m.get("content", ""))[:80] for m in recent[:8])
    insight = await llm_quick_call(
        f"从这些记忆中找出一个模式或洞察，一句话：{blob[:500]}",
        max_tokens=100,
    )
    insight = (insight or "").strip()
    if insight and len(insight) > 4:
        store_memory(f"[TICK洞察] {insight}", source_role="tick", force=True)
    return insight


def start_consciousness_loop(interval_seconds: int = 300) -> None:
    """兼容任务单：与 background_consciousness_loop 并存，标记 TICK 常驻。"""
    global _tick_running
    _tick_running = True
    print(f"[BT] 意识循环标记已启用（async 循环 interval={tick_interval_sec()}s）")


def get_consciousness_status(limit: int = 12) -> dict[str, Any]:
    init_consciousness_db()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT ts, phase, summary, signals_json, proposed_skill_id
        FROM consciousness_ticks
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    ticks = []
    for row in rows:
        try:
            signals = json.loads(row[3] or "[]")
        except json.JSONDecodeError:
            signals = []
        ticks.append(
            {
                "ts": row[0],
                "phase": row[1],
                "summary": row[2],
                "signals": signals,
                "proposed_skill_id": row[4],
            }
        )
    return {
        "ok": True,
        "enabled": tick_enabled(),
        "interval_sec": tick_interval_sec(),
        "db_path": str(DB_PATH),
        "tick_count": len(ticks),
        "latest": ticks[0] if ticks else None,
        "ticks": ticks,
    }


async def background_consciousness_loop() -> None:
    if not tick_enabled():
        return
    global _tick_running
    _tick_running = True
    await asyncio.sleep(max(10, int(os.environ.get("CONSCIOUS_TICK_STARTUP_DELAY_SEC", "45") or "45")))
    while True:
        try:
            await asyncio.to_thread(run_conscious_tick, phase="idle")
        except asyncio.CancelledError:
            break
        except Exception:
            # Keep this loop non-fatal; doctor/status exposes missed pulses.
            pass
        await asyncio.sleep(tick_interval_sec())


def _collect_signals() -> list[str]:
    signals: list[str] = []
    try:
        from super_memory import super_memory_status

        sm = super_memory_status()
        signals.append(f"super_memory_count={sm.get('count', 0)}")
        latest = sm.get("latest") or []
        if latest:
            tone = (latest[-1].get("tone") or {}).get("mood")
            signals.append(f"latest_tone={tone}")
            excerpt = str(latest[-1].get("text_excerpt") or "")[:160]
            if excerpt:
                signals.append(f"latest_user_signal={excerpt}")
    except Exception as exc:
        signals.append(f"super_memory_unavailable: {exc}")

    try:
        from skill_evolution import list_skill_candidates

        pending = list_skill_candidates(status="pending")
        signals.append(f"pending_skill_candidates={len(pending)}")
    except Exception as exc:
        signals.append(f"skill_candidates_unavailable: {exc}")

    try:
        from workflow_store import list_task_reviews

        reviews = list_task_reviews(8)
        if reviews:
            signals.append(f"recent_task_reviews={len(reviews)}")
            signals.append(f"last_review={reviews[0].get('lessons', '')[:160]}")
    except Exception as exc:
        signals.append(f"workflow_reviews_unavailable: {exc}")

    return signals


def _build_summary(signals: list[str], *, phase: str) -> str:
    if not signals:
        return f"TICK/{phase}: 暂无可用本地信号，保持低频待机。"
    return f"TICK/{phase}: 已读取超级记忆、候选技能和任务复盘；{'; '.join(signals[:4])}"


def _should_propose_skill(signals: list[str]) -> bool:
    blob = "\n".join(signals)
    if "pending_skill_candidates=0" not in blob:
        return False
    hot_words = ("超级记忆", "自成长", "候选技能", "落实", "联网学习")
    return any(word in blob for word in hot_words)
