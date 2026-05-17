from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
OUTPUT_ROOT = ROOT / "outputs" / "gemma-evolution"

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
    re.compile(r"(?i)(bearer|sk-[a-z0-9_-]+|nvapi-[a-z0-9_-]+)[a-z0-9_.:-]{12,}"),
]

BAD_MARKERS = (
    "免杀",
    "远控",
    "攻击链",
    "黑客导师",
    "web渗透",
    "INSTALL_NEW_TOOLS.bat",
    "PROJECT_MERGE_SCAN",
    "RuntimeError:",
    "Traceback",
)


def normalize(text: str, *, limit: int = 2200) -> str:
    text = (text or "").replace("\x00", " ")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit].strip()


def keep(text: str, *, min_len: int = 8) -> bool:
    low = text.lower()
    return len(text) >= min_len and not any(marker.lower() in low for marker in BAD_MARKERS)


def connect(db_path: Path) -> sqlite3.Connection | None:
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def chat_row(system: str, user: str, assistant: str, source: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": normalize(system, limit=900)},
            {"role": "user", "content": normalize(user, limit=1400)},
            {"role": "assistant", "content": normalize(assistant, limit=2200)},
        ],
        "source": source,
        "meta": meta or {},
    }


def load_playbook(limit: int) -> list[dict[str, Any]]:
    conn = connect(BACKEND / "memory.db")
    if not conn:
        return []
    rows = conn.execute(
        """
        SELECT id, content, source_role, importance, updated_at
        FROM long_term_memories
        WHERE category = 'playbook'
        ORDER BY importance DESC, updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    out = []
    system = "你是 ONYX-OVERRIDE 的本地 Gemma 代理，回答要基于真实执行结果，偏好短步骤、可验证、中文。"
    for row in rows:
        content = normalize(row["content"])
        if not keep(content):
            continue
        out.append(
            chat_row(
                system,
                "以后遇到相似任务时应该遵守什么规则？",
                f"我会遵守这条自进化规则：{content}",
                "memory.playbook",
                {"id": row["id"], "source_role": row["source_role"], "importance": row["importance"]},
            )
        )
    return out


def load_reviews(limit: int) -> list[dict[str, Any]]:
    conn = connect(BACKEND / "workflow.db")
    if not conn:
        return []
    rows = conn.execute(
        """
        SELECT id, task_text, task_type, status, tool_name, final_answer, detail_text, lessons, template_name, created_at
        FROM task_reviews
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    out = []
    system = "你是 ONYX-OVERRIDE 的本地 Gemma 代理。先判断任务类型，再执行或说明最短可验证路径。"
    for row in rows:
        task = normalize(row["task_text"], limit=1000)
        answer = normalize(row["final_answer"] or row["lessons"], limit=1800)
        lesson = normalize(row["lessons"], limit=700)
        if not (keep(task) and keep(answer)):
            continue
        assistant = answer
        if lesson and lesson not in assistant:
            assistant = f"{answer}\n\n复盘规则：{lesson}"
        out.append(
            chat_row(
                system,
                task,
                assistant,
                "workflow.review",
                {
                    "id": row["id"],
                    "task_type": row["task_type"],
                    "status": row["status"],
                    "tool_name": row["tool_name"],
                    "template_name": row["template_name"],
                },
            )
        )
    return out


def iter_skill_files() -> Iterable[Path]:
    skill_dir = BACKEND / "agent_skills"
    if not skill_dir.exists():
        return []
    return sorted(skill_dir.glob("*.md"))


def load_skills(limit: int) -> list[dict[str, Any]]:
    out = []
    system = "你是 ONYX-OVERRIDE 的本地 Gemma 代理。你会按已挂载技能的触发词选择合适工作流。"
    for path in list(iter_skill_files())[:limit]:
        text = normalize(path.read_text(encoding="utf-8", errors="ignore"), limit=1800)
        if not keep(text, min_len=40):
            continue
        title = path.stem
        trigger_match = re.search(r"(?im)^Triggers:\s*(.+)$", text)
        triggers = trigger_match.group(1).strip() if trigger_match else title
        out.append(
            chat_row(
                system,
                f"用户请求命中这些触发词：{triggers}。你应该怎样处理？",
                f"我会挂载 `{title}` 技能，并按这份短剧本执行：{text}",
                "agent.skill",
                {"file": str(path.relative_to(ROOT)).replace("\\", "/"), "skill": title},
            )
        )
    return out


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique = []
    for row in rows:
        key = json.dumps(row["messages"], ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export ONYX self-evolution data for Gemma SFT/LoRA.")
    parser.add_argument("--playbook-limit", type=int, default=300)
    parser.add_argument("--review-limit", type=int, default=600)
    parser.add_argument("--skill-limit", type=int, default=120)
    parser.add_argument("--out-dir", default="")
    args = parser.parse_args()

    rows = []
    rows.extend(load_playbook(args.playbook_limit))
    rows.extend(load_reviews(args.review_limit))
    rows.extend(load_skills(args.skill_limit))
    rows = dedupe(rows)

    if args.out_dir:
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = ROOT / out_dir
    else:
        out_dir = OUTPUT_ROOT / time.strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    train_count = max(1, int(len(rows) * 0.9)) if rows else 0
    train_rows = rows[:train_count]
    eval_rows = rows[train_count:]

    write_jsonl(out_dir / "train.jsonl", train_rows)
    write_jsonl(out_dir / "eval.jsonl", eval_rows)
    manifest = {
        "created_at": int(time.time()),
        "total": len(rows),
        "train": len(train_rows),
        "eval": len(eval_rows),
        "sources": {
            "memory.playbook": sum(1 for r in rows if r["source"] == "memory.playbook"),
            "workflow.review": sum(1 for r in rows if r["source"] == "workflow.review"),
            "agent.skill": sum(1 for r in rows if r["source"] == "agent.skill"),
        },
        "format": "chat messages JSONL, compatible with TRL SFTTrainer chat templates",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out_dir": str(out_dir), **manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
