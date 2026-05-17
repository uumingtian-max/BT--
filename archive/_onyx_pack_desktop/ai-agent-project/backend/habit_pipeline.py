"""
每天固定时段（默认 9:00 / 21:00 本地）自动执行：
本机体检 → 行为分析 → playbook 写入 → 可选 learned 技能扩展。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sqlite_wal as sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from memory_store import store_playbook_entry

logger = logging.getLogger(__name__)

BEHAVIOR_DB = os.path.join(os.path.dirname(__file__), "behavior.db")
SKILL_DIR = Path(__file__).resolve().parent / "agent_skills"
HABIT_REPORT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "habit_checks"
LEARNED_SKILL_NAME = "learned_habit_auto.md"


def _habit_enabled() -> bool:
    return os.environ.get("HABIT_CHECK_ENABLED", "1").strip().lower() not in ("0", "false", "off", "no")


def _auto_skill_enabled() -> bool:
    return os.environ.get("HABIT_AUTO_SKILL", "1").strip().lower() not in ("0", "false", "off", "no")


def _parse_check_hours() -> list[int]:
    raw = (os.environ.get("HABIT_CHECK_HOURS") or "9,21").strip()
    hours: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        h = int(part)
        if 0 <= h <= 23:
            hours.append(h)
    return sorted(set(hours)) or [9, 21]


def _init_habit_tables() -> None:
    conn = sqlite3.connect(BEHAVIOR_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS habit_check_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            phase TEXT NOT NULL,
            slot_key TEXT NOT NULL,
            doctor_ok INTEGER NOT NULL,
            doctor_failed INTEGER NOT NULL,
            patterns_json TEXT NOT NULL DEFAULT '[]',
            skill_written INTEGER NOT NULL DEFAULT 0,
            summary TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS habit_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_habit_check_slot ON habit_check_log(slot_key)")
    conn.commit()
    conn.close()


_init_habit_tables()


def _meta_get(key: str) -> str | None:
    conn = sqlite3.connect(BEHAVIOR_DB)
    row = conn.execute("SELECT value FROM habit_meta WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else None


def _meta_set(key: str, value: str) -> None:
    conn = sqlite3.connect(BEHAVIOR_DB)
    conn.execute(
        "INSERT INTO habit_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def _slot_key(dt: datetime, hour: int) -> str:
    return dt.strftime("%Y-%m-%d") + f"-{hour:02d}"


def _already_ran_slot(slot_key: str) -> bool:
    conn = sqlite3.connect(BEHAVIOR_DB)
    row = conn.execute("SELECT 1 FROM habit_check_log WHERE slot_key=? LIMIT 1", (slot_key,)).fetchone()
    conn.close()
    return row is not None


def _log_habit_run(
    *,
    phase: str,
    slot_key: str,
    doctor_ok: bool,
    doctor_failed: int,
    patterns: list[str],
    skill_written: bool,
    summary: str,
) -> None:
    conn = sqlite3.connect(BEHAVIOR_DB)
    conn.execute(
        """
        INSERT INTO habit_check_log (ts, phase, slot_key, doctor_ok, doctor_failed, patterns_json, skill_written, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(time.time()),
            phase,
            slot_key,
            1 if doctor_ok else 0,
            doctor_failed,
            json.dumps(patterns, ensure_ascii=False),
            1 if skill_written else 0,
            summary[:12000],
        ),
    )
    conn.commit()
    conn.close()


def _run_doctor() -> dict[str, Any]:
    from meta_routes import meta_doctor

    return meta_doctor()


def maybe_write_learned_skill(patterns: list[str], adjustments: list[str], signals: list[str]) -> bool:
    """行为模式变化时更新 agent_skills/learned_habit_auto.md（自我扩展）。"""
    if not _auto_skill_enabled():
        return False
    blob = "\n".join(patterns + adjustments + signals)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
    if _meta_get("learned_skill_hash") == digest:
        return False

    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    path = SKILL_DIR / LEARNED_SKILL_NAME
    trigger_bits = ["习惯", "行为画像", "自进化", "定时体检", "learned"]
    trigger_bits.extend(signals[:8])
    triggers = ",".join(dict.fromkeys(trigger_bits))

    lines = [
        "# 从本机行为自动学习的习惯（勿手改，由 habit_pipeline 覆盖）",
        "",
        f"Triggers: {triggers}",
        "",
        "---",
        "",
        "以下由每日两次习惯体检根据窗口/进程/工具成功率推断，供 Agent 自动挂载：",
        "",
        "## 当前行为模式",
    ]
    lines.extend(f"- {p}" for p in patterns[:12])
    lines.append("")
    lines.append("## 建议执行调整")
    lines.extend(f"- {a}" for a in adjustments[:10])
    lines.append("")
    lines.append("## 关联本机能力")
    lines.append("- 体检：`GET /meta/doctor` · 画像：`GET /observe/evolution` · 手动复检：`POST /meta/habit/run`")
    lines.append(f"- 上次更新：{time.strftime('%Y-%m-%d %H:%M', time.localtime())}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _meta_set("learned_skill_hash", digest)
    _meta_set("learned_skill_updated_at", str(int(time.time())))
    return True


def _skill_quality_snapshot() -> dict[str, int]:
    """技能库结构质检（Skill Creator 六段 + 自测用语覆盖率）。"""
    total = 0
    structured = 0
    with_eval = 0
    if not SKILL_DIR.is_dir():
        return {"total": 0, "structured": 0, "with_eval": 0}
    for path in SKILL_DIR.glob("*.md"):
        if path.name == LEARNED_SKILL_NAME:
            continue
        total += 1
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "## 执行步骤" in raw and "**何时使用**" in raw:
            structured += 1
        if "自测用语" in raw:
            with_eval += 1
    return {"total": total, "structured": structured, "with_eval": with_eval}


def run_habit_check(*, phase: str = "manual", slot_key: str | None = None) -> dict[str, Any]:
    """
    一次完整习惯流水线：doctor → 行为推断 → 日报 → playbook → 可选 learned 技能。
    """
    from observe import get_evolution_profile_text, infer_behavior_patterns, upsert_daily_report

    if slot_key is None:
        now = datetime.now()
        slot_key = _slot_key(now, now.hour)

    doctor = _run_doctor()
    doctor_ok = bool(doctor.get("ok"))
    doctor_failed = int(doctor.get("failed_count") or 0)
    failed_names = [c["name"] for c in (doctor.get("checks") or []) if c.get("status") != "ok"]

    behavior = infer_behavior_patterns()
    patterns = list(behavior.get("patterns") or [])
    adjustments = list(behavior.get("adjustments") or [])
    signals = list(behavior.get("signals") or [])

    report = upsert_daily_report()
    skill_written = maybe_write_learned_skill(patterns, adjustments, signals)

    evolve_result: dict[str, Any] | None = None
    if os.environ.get("HABIT_EVOLVE_ON_CHECK", "0").strip() in ("1", "true", "yes"):
        try:
            from self_evolve import distill_playbook_with_llm

            evolve_result = distill_playbook_with_llm()
        except Exception as e:
            evolve_result = {"ok": False, "error": str(e)}

    profile_excerpt = get_evolution_profile_text()[:1500]
    skill_q = _skill_quality_snapshot()
    summary_lines = [
        f"# 习惯体检 · {phase} · {time.strftime('%Y-%m-%d %H:%M', time.localtime())}",
        "",
        f"- 本机体检：{'通过' if doctor_ok else f'{doctor_failed} 项未通过'}",
        f"- 技能库：{skill_q['total']} 条 · 结构化 {skill_q['structured']} · 含自测用语 {skill_q['with_eval']}",
    ]
    if failed_names:
        summary_lines.append(f"- 未通过项：{', '.join(failed_names[:8])}")
    summary_lines.append(f"- 行为模式条数：{len(patterns)}")
    if skill_written:
        summary_lines.append(f"- 已更新技能：`agent_skills/{LEARNED_SKILL_NAME}`")
    summary_lines.extend(["", "## 行为摘要", *[f"- {p}" for p in patterns[:6]]])
    summary = "\n".join(summary_lines)

    playbook_line = (
        f"[习惯体检·{phase}] 体检={'OK' if doctor_ok else f'FAIL({doctor_failed})'}；"
        + (patterns[0][:80] if patterns else "无显著模式")
    )
    store_playbook_entry(playbook_line, source_session_id="habit", source_role="habit_check", importance=4)

    HABIT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = HABIT_REPORT_DIR / f"{slot_key.replace(':', '-')}.md"
    report_path.write_text(summary + "\n\n---\n\n" + profile_excerpt, encoding="utf-8")

    _log_habit_run(
        phase=phase,
        slot_key=slot_key,
        doctor_ok=doctor_ok,
        doctor_failed=doctor_failed,
        patterns=patterns,
        skill_written=skill_written,
        summary=summary,
    )

    webhook = (os.environ.get("HABIT_WEBHOOK_URL") or os.environ.get("SCHEDULER_WEBHOOK_URL") or os.environ.get("WEBHOOK_URL") or "").strip()
    if webhook:
        try:
            import httpx

            httpx.post(
                webhook,
                json={
                    "event": "habit_check_done",
                    "phase": phase,
                    "doctor_ok": doctor_ok,
                    "doctor_failed": doctor_failed,
                    "skill_written": skill_written,
                    "summary": summary[:4000],
                },
                timeout=20.0,
            )
        except Exception as e:
            logger.warning("habit webhook failed: %s", e)

    return {
        "ok": True,
        "phase": phase,
        "slot_key": slot_key,
        "doctor": {"ok": doctor_ok, "failed_count": doctor_failed, "failed": failed_names},
        "behavior": {"patterns": patterns, "signals": signals, "adjustments": adjustments},
        "daily_report": report,
        "skill_written": skill_written,
        "learned_skill": LEARNED_SKILL_NAME if skill_written else None,
        "skill_quality": skill_q,
        "report_path": str(report_path),
        "evolve": evolve_result,
        "summary": summary,
    }


def get_habit_status() -> dict[str, Any]:
    hours = _parse_check_hours()
    last = None
    conn = sqlite3.connect(BEHAVIOR_DB)
    row = conn.execute(
        "SELECT ts, phase, doctor_ok, doctor_failed, skill_written, substr(summary,1,400) FROM habit_check_log ORDER BY ts DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        last = {
            "ts": row[0],
            "phase": row[1],
            "doctor_ok": bool(row[2]),
            "doctor_failed": row[3],
            "skill_written": bool(row[4]),
            "summary_preview": row[5],
        }
    learned_path = SKILL_DIR / LEARNED_SKILL_NAME
    return {
        "ok": True,
        "enabled": _habit_enabled(),
        "check_hours_local": hours,
        "auto_skill": _auto_skill_enabled(),
        "learned_skill_file": LEARNED_SKILL_NAME if learned_path.is_file() else None,
        "learned_skill_updated_at": _meta_get("learned_skill_updated_at"),
        "last_run": last,
        "report_dir": str(HABIT_REPORT_DIR),
    }


def _seconds_until_next_slot(hours: list[int]) -> tuple[float, str, str]:
    now = datetime.now()
    candidates: list[tuple[datetime, str]] = []
    for h in hours:
        slot = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if slot > now:
            phase = "morning" if h < 12 else "evening"
            candidates.append((slot, phase))
    if candidates:
        nxt, phase = min(candidates, key=lambda x: x[0])
        return (nxt - now).total_seconds(), phase, _slot_key(nxt, nxt.hour)
    tomorrow = now + timedelta(days=1)
    h0 = hours[0]
    nxt = tomorrow.replace(hour=h0, minute=0, second=0, microsecond=0)
    phase = "morning" if h0 < 12 else "evening"
    return (nxt - now).total_seconds(), phase, _slot_key(nxt, h0)


async def background_habit_loop() -> None:
    if not _habit_enabled():
        return
    hours = _parse_check_hours()
    # 启动后 90 秒内若错过当日时段，不补跑（避免重启风暴）；仅等待下一时段
    await asyncio.sleep(8)
    while True:
        try:
            wait_sec, phase, slot_key = _seconds_until_next_slot(hours)
            wait_sec = max(5.0, wait_sec)
            await asyncio.sleep(wait_sec)
            if _already_ran_slot(slot_key):
                await asyncio.sleep(60)
                continue
            await asyncio.to_thread(run_habit_check, phase=phase, slot_key=slot_key)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("habit_check loop error")
            await asyncio.sleep(120)


def ensure_scheduler_habit_jobs() -> None:
    """在定时任务列表中注册可见的 habit 任务（实际由 background_habit_loop 触发）。"""
    from scheduler_store import create_job, list_jobs

    existing = list_jobs()
    if any((j.get("task_kind") or "") == "habit_check" for j in existing):
        return
    hours = _parse_check_hours()
    for h in hours:
        phase = "morning" if h < 12 else "evening"
        create_job(
            name=f"习惯体检 {h:02d}:00",
            message=f"[habit:auto] {phase}",
            interval_sec=86400,
            task_kind="habit_check",
            enabled=False,
        )
