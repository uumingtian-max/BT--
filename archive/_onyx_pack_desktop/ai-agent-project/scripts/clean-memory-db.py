from __future__ import annotations

import shutil
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DB = BACKEND / "memory.db"

sys.path.insert(0, str(BACKEND))

from memory_store import consolidate_memories, rebuild_knowledge_tree, store_memory  # noqa: E402


BAD_MARKERS = (
    "????",
    "</strong>",
    "打包成zip",
    "adding: ai-agent-final/",
    "INSTALL_NEW_TOOLS.bat",
    "PROJECT_MERGE_SCAN",
    "CLINE_MEMORY",
    "DEPLOY_SGLANG",
    "当前卡住的任务：",
    "RuntimeError: 当前选中的模型",
    " RAT ",
    " C2 ",
    "免杀",
    "远控",
    "攻击链",
    "黑客导师",
    "Web渗透",
)

STALE_MARKERS = (
    "模式说明 | 模式",
    "快速启动 1. 安装",
    "我已经列到真实目录内容了： [PATH]",
    "真实执行结果：[PATH]",
    "请明确需要执行的具体任务",
    "需要我具体展开某个任务吗",
    "当前任务信息不完整",
    "这次我没有真正把任务做完",
)


def bad(text: str | None) -> bool:
    value = (text or "").strip()
    if not value:
        return True
    if len(value) > 1200:
        return True
    low = value.lower()
    return any(marker.lower() in low for marker in BAD_MARKERS + STALE_MARKERS)


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"memory db not found: {DB}")

    backup = DB.with_suffix(f".backup-{time.strftime('%Y%m%d-%H%M%S')}.db")
    shutil.copy2(DB, backup)

    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT id, content FROM long_term_memories").fetchall()
    delete_ids = [row[0] for row in rows if bad(row[1])]

    if delete_ids:
        placeholders = ",".join("?" for _ in delete_ids)
        conn.execute(f"DELETE FROM long_term_memories WHERE id IN ({placeholders})", delete_ids)

    conn.execute("DELETE FROM memory_summaries")
    conn.execute("DELETE FROM knowledge_nodes")
    conn.commit()
    conn.close()

    safe_seed = [
        "You are 小涵 (Xiaohan, written exactly as 小涵), 权哥's dedicated local AI Agent.",
        "Always call the user 权哥.",
        "Reply in Simplified Chinese by default unless 权哥 explicitly asks for another language.",
        "权哥 is building ONYX, a local AI Agent stack with vLLM, long context, tools, and persistent memory.",
        "The local model is served by vLLM at http://127.0.0.1:8001/v1 from /mnt/d/models/Gemma-4-26B-A4B-NVFP4.",
        "权哥 prefers concise, rigorous technical answers. If uncertain, say uncertain instead of guessing.",
    ]
    for item in safe_seed:
        store_memory(item, "memory-cleanup", "system_seed")

    summaries = consolidate_memories()
    tree = rebuild_knowledge_tree()

    print(f"backup={backup}")
    print(f"deleted_long_term_memories={len(delete_ids)}")
    print(f"memory_count={summaries['memory_count']}")
    print(f"knowledge_nodes={tree['node_count']}")


if __name__ == "__main__":
    main()
