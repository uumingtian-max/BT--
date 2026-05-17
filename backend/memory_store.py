from __future__ import annotations

import logging

import json
import os
import re
import sqlite_wal as sqlite3
import threading
import time
from collections import Counter
from typing import Any

_logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")
from paths import LEGACY_VAULT_DIR, VAULT_DIR

if not VAULT_DIR.is_dir() and LEGACY_VAULT_DIR.is_dir():
    VAULT_DIR = LEGACY_VAULT_DIR


def init_memory_store() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS long_term_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            source_session_id TEXT,
            source_role TEXT,
            importance INTEGER NOT NULL DEFAULT 3,
            tags_json TEXT NOT NULL DEFAULT '[]',
            access_count INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            last_accessed_at INTEGER NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_long_term_memories_updated_at ON long_term_memories(updated_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_long_term_memories_category ON long_term_memories(category)")
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='long_term_memories_fts'").fetchone()
    if not row:
        conn.execute(
            """
            CREATE VIRTUAL TABLE long_term_memories_fts USING fts5(
                content,
                category UNINDEXED,
                content='long_term_memories',
                content_rowid='id',
                tokenize='unicode61'
            )
            """
        )
        conn.execute(
            """
            INSERT INTO long_term_memories_fts(rowid, content, category)
            SELECT id, content, category FROM long_term_memories
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS ltm_fts_ai AFTER INSERT ON long_term_memories BEGIN
              INSERT INTO long_term_memories_fts(rowid, content, category)
              VALUES (new.id, new.content, new.category);
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS ltm_fts_ad AFTER DELETE ON long_term_memories BEGIN
              INSERT INTO long_term_memories_fts(long_term_memories_fts, rowid, content, category)
              VALUES ('delete', old.id, old.content, old.category);
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS ltm_fts_au AFTER UPDATE ON long_term_memories BEGIN
              INSERT INTO long_term_memories_fts(long_term_memories_fts, rowid, content, category)
              VALUES ('delete', old.id, old.content, old.category);
              INSERT INTO long_term_memories_fts(rowid, content, category)
              VALUES (new.id, new.content, new.category);
            END
            """
        )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            source_count INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL UNIQUE,
            parent_scope TEXT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_memory_store()


def _now_ts() -> int:
    return int(time.time())


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


_BAD_MEMORY_MARKERS = (
    "????",
    "</strong>",
    "打包成zip",
    "adding: ai-agent-final/",
    "INSTALL_NEW_TOOLS.bat",
    "PROJECT_MERGE_SCAN",
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


def _is_bad_memory(text: str) -> bool:
    normalized = _normalize_text(text)
    if not normalized:
        return True
    if len(normalized) > 3000:
        return True
    lower = normalized.lower()
    return any(marker.lower() in lower for marker in _BAD_MEMORY_MARKERS)


def _extract_tags(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_.:+#-]{2,}|[\u4e00-\u9fff]{2,8}", text.lower())
    stop = {
        "这个",
        "那个",
        "我们",
        "你们",
        "他们",
        "然后",
        "因为",
        "所以",
        "现在",
        "最近",
        "就是",
        "一个",
        "已经",
        "可以",
        "需要",
        "希望",
        "桌面",
        "文档",
        "下载",
        "图片",
        "视频",
    }
    counter = Counter(t for t in tokens if t not in stop)
    return [token for token, _ in counter.most_common(8)]


def _classify_memory(text: str) -> tuple[str, int]:
    if any(
        k in text
        for k in [
            "[自进化复盘]",
            "[playbook]",
            "复盘规则",
            "self_evolve",
            "distill_playbook",
            "[自进化蒸馏]",
        ]
    ):
        return "playbook", 5
    if any(k in text for k in ["我叫", "我的名字", "我是", "You are", "Always call the user"]):
        return "identity", 5
    if any(
        k in text
        for k in [
            "我喜欢",
            "我习惯",
            "偏好",
            "默认",
            "以后都",
            "记住",
            "prefers",
            "Reply in",
        ]
    ):
        return "preference", 5
    if any(
        k in text
        for k in [
            "我现在在做",
            "最近在做",
            "项目",
            "任务",
            "正在做",
            "要做",
            "building",
            "local AI Agent",
        ]
    ):
        return "project", 4
    if any(
        k in text
        for k in [
            "我的设备",
            "显卡",
            "RTX",
            "GPU",
            "CPU",
            "内存",
            "Ollama",
            "vLLM",
            "model is served",
        ]
    ):
        return "device", 4
    return "fact", 3


def _looks_memorable(text: str) -> bool:
    if len(text) < 6:
        return False
    rules = [
        "记住",
        "以后",
        "默认",
        "偏好",
        "习惯",
        "我叫",
        "我是",
        "我喜欢",
        "我的设备",
        "我现在在做",
        "最近在做",
        "项目",
        "任务",
        "显卡",
        "GPU",
        "CPU",
        "Ollama",
        "You are",
        "Always call the user",
        "Reply in",
        "prefers",
        "building",
        "local AI Agent",
        "vLLM",
    ]
    return any(rule in text for rule in rules)


def store_memory(
    content: str,
    source_session_id: str | None = None,
    source_role: str | None = None,
    *,
    _conn: sqlite3.Connection | None = None,
) -> dict[str, Any] | None:
    """写入一条长期记忆。可传入外部连接 _conn 以批量共享同一事务。"""
    text = _normalize_text(content)
    if _is_bad_memory(text):
        return None
    if not _looks_memorable(text):
        return None

    category, importance = _classify_memory(text)
    tags = _extract_tags(text)
    ts = _now_ts()

    own_conn = _conn is None
    conn = sqlite3.connect(DB_PATH) if own_conn else _conn
    try:
        existing = conn.execute(
            "SELECT id, content, importance, access_count FROM long_term_memories WHERE content = ? LIMIT 1",
            (text,),
        ).fetchone()

        if existing:
            memory_id = existing[0]
            conn.execute(
                """
                UPDATE long_term_memories
                SET importance = MAX(importance, ?),
                    updated_at = ?,
                    last_accessed_at = ?,
                    access_count = access_count + 1
                WHERE id = ?
                """,
                (importance, ts, ts, memory_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO long_term_memories (
                    category, content, source_session_id, source_role, importance,
                    tags_json, access_count, created_at, updated_at, last_accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    category,
                    text,
                    source_session_id,
                    source_role,
                    importance,
                    json.dumps(tags, ensure_ascii=False),
                    1,
                    ts,
                    ts,
                    ts,
                ),
            )
        if own_conn:
            conn.commit()
    finally:
        if own_conn:
            conn.close()
    return {
        "category": category,
        "content": text,
        "importance": importance,
        "tags": tags,
    }


def remember_from_message(session_id: str, role: str, content: str) -> list[dict[str, Any]]:
    memories: list[dict[str, Any]] = []
    text = _normalize_text(content)
    if not text:
        return memories

    chunks = re.split(r"[。！？!\n]+", text)
    # 所有 chunk 共享一个连接，避免每条独立开关连接
    conn = sqlite3.connect(DB_PATH)
    try:
        for chunk in chunks:
            cleaned = re.sub(r"^(?:记住[:：]|请记住[:：])\s*", "", chunk.strip())
            item = store_memory(cleaned, session_id, role, _conn=conn)
            if item:
                memories.append(item)
        conn.commit()
    finally:
        conn.close()
    return memories


def _strip_task_annotation(text: str) -> str:
    """去掉复盘末尾「（相关任务：xxx）」等尾注，便于语义去重。"""
    return re.sub(r"（相关任务：.*?）\s*$", "", text).strip()


def store_playbook_entry(
    content: str,
    *,
    source_session_id: str = "agent",
    source_role: str = "self_evolve",
    importance: int = 5,
) -> dict[str, Any] | None:
    """写入自进化剧本；精确或语义去重时合并重要度，仍返回 dict 供调用方判断成功。"""
    text = _normalize_text(content)
    if len(text) < 12 or len(text) > 900 or _is_bad_memory(text):
        return None
    category = "playbook"
    tags = list(dict.fromkeys(_extract_tags(text) + ["playbook", "self_evolve"]))
    ts = _now_ts()
    core = _strip_task_annotation(text)
    core_prefix = core[:80] if core else ""

    conn = sqlite3.connect(DB_PATH)
    existing = conn.execute(
        "SELECT id, importance FROM long_term_memories WHERE category = ? AND content = ? LIMIT 1",
        (category, text),
    ).fetchone()
    if not existing and core_prefix:
        existing = conn.execute(
            """
            SELECT id, importance FROM long_term_memories
            WHERE category = ? AND (content LIKE ? OR content = ?)
            LIMIT 1
            """,
            (category, core_prefix + "%", core),
        ).fetchone()

    if existing:
        memory_id, imp = existing[0], existing[1]
        new_imp = max(imp, importance)
        conn.execute(
            """
            UPDATE long_term_memories
            SET importance = MAX(importance, ?), updated_at = ?, last_accessed_at = ?, access_count = access_count + 1
            WHERE id = ?
            """,
            (importance, ts, ts, memory_id),
        )
        conn.commit()
        conn.close()
        return {
            "category": category,
            "content": text,
            "importance": new_imp,
            "tags": tags,
            "merged": True,
        }

    conn.execute(
        """
        INSERT INTO long_term_memories (
            category, content, source_session_id, source_role, importance,
            tags_json, access_count, created_at, updated_at, last_accessed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            category,
            text,
            source_session_id,
            source_role,
            importance,
            json.dumps(tags, ensure_ascii=False),
            1,
            ts,
            ts,
            ts,
        ),
    )
    conn.commit()
    conn.close()
    return {
        "category": category,
        "content": text,
        "importance": importance,
        "tags": tags,
    }


def list_playbook_entries(limit: int = 40) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT id, content, importance, tags_json, updated_at
        FROM long_term_memories
        WHERE category = 'playbook'
        ORDER BY importance DESC, updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "content": row[1],
            "importance": row[2],
            "tags": json.loads(row[3] or "[]"),
            "updated_at": row[4],
        }
        for row in rows
    ]


def build_playbook_context(query: str, limit: int = 5) -> str:
    q = _normalize_text(query).lower()
    q_tags = set(_extract_tags(q))
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT id, content, importance, tags_json, updated_at
        FROM long_term_memories
        WHERE category = 'playbook'
        ORDER BY updated_at DESC
        LIMIT 80
        """,
    ).fetchall()
    conn.close()
    scored: list[tuple[float, tuple[Any, ...]]] = []
    for row in rows:
        if _is_bad_memory(row[1] or ""):
            continue
        tags = set(json.loads(row[3] or "[]"))
        content = (row[1] or "").lower()
        overlap = len(q_tags & tags)
        score = row[2] * 4 + overlap * 6 + (8 if q and q in content else 0)
        if overlap > 0 or (q and q in content):
            scored.append((score, row))
    scored.sort(key=lambda x: (-x[0], -x[1][4]))
    top = [r for _, r in scored[:limit]]
    if not top:
        return ""
    lines = ["## 自进化剧本（从近期任务复盘提炼，优先遵守）"]
    for row in top:
        lines.append(f"- {row[1]}")
    return "\n".join(lines)


def _fts_memory_query(raw: str) -> str | None:
    q = _normalize_text(raw)
    if len(q) < 2:
        return None
    q = re.sub(r"[\"\'*]", " ", q).strip()
    return q or None


def search_memories(query: str, limit: int = 6) -> list[dict[str, Any]]:
    q = _normalize_text(query).lower()
    q_tags = set(_extract_tags(q))
    conn = sqlite3.connect(DB_PATH)

    # 只做一次全表扫，兼作 FTS miss 和 scored 为空两种回退的数据源
    fallback_rows: list[Any] = []
    rows: list[Any] = []
    fts_q = _fts_memory_query(query)
    fts_ok = False
    if fts_q:
        try:
            rows = conn.execute(
                """
                SELECT m.id, m.category, m.content, m.importance, m.tags_json, m.access_count, m.updated_at, m.last_accessed_at
                FROM long_term_memories_fts AS ltmf
                JOIN long_term_memories m ON m.id = ltmf.rowid
                WHERE ltmf MATCH ?
                ORDER BY bm25(ltmf)
                LIMIT ?
                """,
                (fts_q, limit * 6),
            ).fetchall()
            fts_ok = bool(rows)
        except sqlite3.OperationalError:
            rows = []

    if not fts_ok:
        # 全表扫一次，同时作为 scored 为空时的稳定类别回退
        fallback_rows = conn.execute(
            """
            SELECT id, category, content, importance, tags_json, access_count, updated_at, last_accessed_at
            FROM long_term_memories
            ORDER BY updated_at DESC
            LIMIT 200
            """
        ).fetchall()
        rows = fallback_rows

    scored: list[tuple[float, tuple[Any, ...]]] = []
    for row in rows:
        if _is_bad_memory(row[2] or ""):
            continue
        tags = set(json.loads(row[4] or "[]"))
        content = (row[2] or "").lower()
        overlap = len(q_tags & tags)
        score = row[3] * 3 + overlap * 5 + row[5]
        if q and q in content:
            score += 8
        if overlap > 0 or (q and any(token in content for token in q_tags)):
            scored.append((score, row))

    if not scored:
        # 复用已拿到的 fallback_rows（FTS miss 时已有），否则补一次查询
        if not fallback_rows:
            fallback_rows = conn.execute(
                """
                SELECT id, category, content, importance, tags_json, access_count, updated_at, last_accessed_at
                FROM long_term_memories
                ORDER BY updated_at DESC
                LIMIT 200
                """
            ).fetchall()
        stable_categories = {"identity", "preference", "device"}
        scored = [
            (row[3] * 3 + row[5], row)
            for row in fallback_rows
            if row[1] in stable_categories and not _is_bad_memory(row[2] or "")
        ][:limit]

    scored.sort(key=lambda x: (-x[0], -x[1][6]))
    top = scored[:limit]

    out: list[dict[str, Any]] = []
    ts = _now_ts()
    for _, row in top:
        conn.execute(
            "UPDATE long_term_memories SET access_count = access_count + 1, last_accessed_at = ? WHERE id = ?",
            (ts, row[0]),
        )
        out.append(
            {
                "id": row[0],
                "category": row[1],
                "content": row[2],
                "importance": row[3],
                "tags": json.loads(row[4] or "[]"),
                "access_count": row[5] + 1,
                "updated_at": row[6],
            }
        )
    conn.commit()
    conn.close()
    return out


def build_memory_context(query: str, limit: int = 6) -> str:
    memories = search_memories(query, limit=limit)
    if not memories:
        return ""
    lines = ["## 相关长期记忆"]
    for item in memories:
        lines.append(f"- [{item['category']}] {item['content']} (重要度 {item['importance']}/5)")
    return "\n".join(lines)


def list_memories(limit: int = 50) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT id, category, content, importance, tags_json, access_count, updated_at
        FROM long_term_memories
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "category": row[1],
            "content": row[2],
            "importance": row[3],
            "tags": json.loads(row[4] or "[]"),
            "access_count": row[5],
            "updated_at": row[6],
        }
        for row in rows
        if not _is_bad_memory(row[2] or "")
    ]


def _upsert_summary(scope: str, title: str, summary: str, source_count: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO memory_summaries (scope, title, summary, source_count, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(scope) DO UPDATE SET
            title = excluded.title,
            summary = excluded.summary,
            source_count = excluded.source_count,
            updated_at = excluded.updated_at
        """,
        (scope, title, summary, source_count, _now_ts()),
    )
    conn.commit()
    conn.close()


def _upsert_knowledge_node(scope: str, title: str, body: str, level: int = 0, parent_scope: str | None = None) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO knowledge_nodes (scope, parent_scope, title, body, level, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(scope) DO UPDATE SET
            parent_scope = excluded.parent_scope,
            title = excluded.title,
            body = excluded.body,
            level = excluded.level,
            updated_at = excluded.updated_at
        """,
        (scope, parent_scope, title, body, level, _now_ts()),
    )
    conn.commit()
    conn.close()


def ingest_notebook_corpus(title: str, body: str) -> dict[str, Any]:
    """NotebookLM-style: compress long corpus into knowledge tree under notebook:<slug>."""
    from context_pack import compress_for_llm

    safe = _normalize_text(title) or "Notebook"
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", safe)[:48].strip("_") or "notebook"
    scope = f"notebook:{slug}"
    packed = compress_for_llm(body or "", 14000, "notebook")
    _upsert_knowledge_node(scope, safe, packed, level=1, parent_scope="root")
    return {"ok": True, "scope": scope, "chars": len(packed)}


def consolidate_memories() -> dict[str, Any]:
    items = list_memories(200)
    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_category.setdefault(item["category"], []).append(item)

    summaries: list[dict[str, Any]] = []
    for category, rows in by_category.items():
        title = {
            "identity": "身份记忆",
            "preference": "偏好记忆",
            "project": "项目记忆",
            "device": "设备记忆",
            "fact": "一般事实记忆",
            "playbook": "自进化剧本",
        }.get(category, f"{category} 记忆")
        top_rows = rows[:6]
        summary = "\n".join(f"- {row['content']}" for row in top_rows) if top_rows else "暂无可总结内容。"
        _upsert_summary(f"category:{category}", title, summary, len(rows))
        summaries.append(
            {
                "scope": f"category:{category}",
                "title": title,
                "summary": summary,
                "source_count": len(rows),
            }
        )

    overall_summary = (
        "这段时间形成的长期记忆重点：\n" + "\n".join(f"- [{item['category']}] {item['content']}" for item in items[:10])
        if items
        else "目前还没有足够的长期记忆。"
    )
    _upsert_summary("overall", "总体记忆摘要", overall_summary, len(items))

    return {
        "ok": True,
        "memory_count": len(items),
        "category_count": len(by_category),
        "summaries": summaries,
        "overall_summary": overall_summary,
    }


def list_memory_summaries() -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT scope, title, summary, source_count, updated_at
        FROM memory_summaries
        ORDER BY updated_at DESC
        """
    ).fetchall()
    conn.close()
    return [
        {
            "scope": row[0],
            "title": row[1],
            "summary": row[2],
            "source_count": row[3],
            "updated_at": row[4],
        }
        for row in rows
    ]


def list_knowledge_nodes() -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT scope, parent_scope, title, body, level, updated_at
        FROM knowledge_nodes
        ORDER BY level ASC, scope ASC
        """
    ).fetchall()
    conn.close()
    return [
        {
            "scope": row[0],
            "parent_scope": row[1],
            "title": row[2],
            "body": row[3],
            "level": row[4],
            "updated_at": row[5],
        }
        for row in rows
    ]


def get_knowledge_tree_info() -> dict[str, int]:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS node_count,
            SUM(CASE WHEN level = 1 AND scope LIKE 'category:%' THEN 1 ELSE 0 END) AS category_count
        FROM knowledge_nodes
        """
    ).fetchone()
    conn.close()
    return {
        "node_count": int(row[0] or 0),
        "category_count": int(row[1] or 0),
    }


def _score_knowledge_node(query: str, node: dict[str, Any]) -> float:
    q = _normalize_text(query).lower()
    tags = set(_extract_tags(q))
    haystack = f"{node.get('title', '')}\n{node.get('body', '')}".lower()
    overlap = sum(1 for tag in tags if tag and tag in haystack)
    score = overlap * 5
    if q and q in haystack:
        score += 8
    score += max(0, 3 - int(node.get("level", 0)))
    return score


def rebuild_knowledge_tree() -> dict[str, Any]:
    items = list_memories(300)
    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_category.setdefault(item["category"], []).append(item)

    overall_lines = ["# 长期知识树", "", "## 总览"]
    overall_lines.append(f"- 记忆总数：{len(items)}")
    overall_lines.append(f"- 分类数：{len(by_category)}")

    _upsert_knowledge_node("root", "长期知识树", "\n".join(overall_lines), level=0, parent_scope=None)

    for category, rows in by_category.items():
        title = {
            "identity": "身份知识",
            "preference": "偏好知识",
            "project": "项目知识",
            "device": "设备知识",
            "fact": "一般知识",
            "playbook": "自进化剧本",
        }.get(category, f"{category} 知识")
        body_lines = [f"# {title}", "", "## 摘要"]
        top_rows = rows[:12]
        for row in top_rows:
            body_lines.append(f"- {row['content']}")
        if not top_rows:
            body_lines.append("- 暂无内容")
        _upsert_knowledge_node(
            f"category:{category}",
            title,
            "\n".join(body_lines),
            level=1,
            parent_scope="root",
        )

        for row in top_rows:
            detail_lines = [
                f"# 记忆条目 {row['id']}",
                "",
                f"- 分类：{row['category']}",
                f"- 重要度：{row['importance']}/5",
                f"- 标签：{', '.join(row.get('tags', [])) or '无'}",
                "",
                "## 内容",
                row["content"],
            ]
            _upsert_knowledge_node(
                f"memory:{row['id']}",
                row["content"][:60],
                "\n".join(detail_lines),
                level=2,
                parent_scope=f"category:{category}",
            )

    return {
        "node_count": len(list_knowledge_nodes()),
        "category_count": len(by_category),
        "memory_count": len(items),
    }


_knowledge_tree_rebuild_lock = threading.Lock()
_knowledge_tree_rebuild_scheduled = False


def _schedule_knowledge_tree_rebuild() -> None:
    """在后台线程重建知识树，避免阻塞请求路径。"""
    global _knowledge_tree_rebuild_scheduled
    with _knowledge_tree_rebuild_lock:
        if _knowledge_tree_rebuild_scheduled:
            return
        _knowledge_tree_rebuild_scheduled = True

    def _run() -> None:
        global _knowledge_tree_rebuild_scheduled
        try:
            rebuild_knowledge_tree()
        except Exception:
            _logger.exception("rebuild_knowledge_tree 出错")
        finally:
            with _knowledge_tree_rebuild_lock:
                _knowledge_tree_rebuild_scheduled = False

    threading.Thread(target=_run, daemon=True).start()


def build_knowledge_context(query: str, limit: int = 5) -> str:
    nodes = list_knowledge_nodes()
    if not nodes:
        # 调度后台重建，本次请求直接返回空，不阻塞
        _schedule_knowledge_tree_rebuild()
        return ""
    scored = []
    for node in nodes:
        score = _score_knowledge_node(query, node)
        if score > 0:
            scored.append((score, node))
    if not scored:
        scored = [(1, node) for node in nodes[:limit]]
    scored.sort(key=lambda x: (-x[0], x[1].get("level", 0), x[1].get("scope", "")))
    picked = [node for _, node in scored[:limit]]
    lines = ["## 相关知识库上下文"]
    for node in picked:
        body = (node.get("body") or "").strip()
        if len(body) > 260:
            body = body[:260] + "..."
        lines.append(f"- [{node.get('scope')}] {body}")
    return "\n".join(lines)


def export_memory_vault() -> dict[str, Any]:
    import hashlib

    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    nodes = list_knowledge_nodes()
    if not nodes:
        _schedule_knowledge_tree_rebuild()
        return {"vault_dir": str(VAULT_DIR), "files_written": 0, "index_file": ""}

    written: list[str] = []
    skipped = 0
    for node in nodes:
        safe_name = re.sub(r"[<>:\"/\\\\|?*]+", "_", node["scope"])
        path = VAULT_DIR / f"{safe_name}.md"
        new_body = node["body"]
        # 只在内容变化时写文件，避免每次 10min 维护循环写几百个文件
        if path.exists():
            old_hash = hashlib.md5(path.read_bytes()).hexdigest()
            new_hash = hashlib.md5(new_body.encode("utf-8")).hexdigest()
            if old_hash == new_hash:
                skipped += 1
                continue
        path.write_text(new_body, encoding="utf-8")
        written.append(str(path))

    index_lines = [
        "# Knowledge Vault",
        "",
        "## Nodes",
    ]
    for node in nodes:
        index_lines.append(f"- {node['scope']} -> {node['title']}")
    index_path = VAULT_DIR / "index.md"
    index_path.write_text("\n".join(index_lines), encoding="utf-8")
    written.append(str(index_path))
    return {
        "vault_dir": str(VAULT_DIR),
        "files_written": len(written),
        "files_skipped": skipped,
        "index_file": str(index_path),
    }


def refresh_integrated_knowledge() -> dict[str, Any]:
    tree_info = rebuild_knowledge_tree()
    summaries = list_memory_summaries()
    summary_lines = ["# 系统知识总览", "", "## 记忆摘要"]
    for item in summaries[:8]:
        summary_lines.append(f"### {item['title']}")
        summary_lines.append(item["summary"])
        summary_lines.append("")

    try:
        from workflow_store import get_workflow_dashboard

        workflow_dash = get_workflow_dashboard()
        summary_lines.append("## 任务复盘")
        summary_lines.append(f"- 复盘总数：{workflow_dash.get('review_count', 0)}")
        for item in workflow_dash.get("recent_reviews", [])[:6]:
            summary_lines.append(f"- [{item.get('status')}] {item.get('task_type')} / {item.get('lessons')}")
    except Exception:
        _logger.warning("获取 workflow dashboard 失败", exc_info=True)
        workflow_dash = {}

    try:
        from observe import infer_behavior_patterns

        evo = infer_behavior_patterns()
        summary_lines.append("")
        summary_lines.append("## 自进化模式")
        for item in evo.get("patterns", [])[:6]:
            summary_lines.append(f"- {item}")
        for item in evo.get("adjustments", [])[:6]:
            summary_lines.append(f"- 调整：{item}")
    except Exception:
        _logger.warning("infer_behavior_patterns 失败", exc_info=True)
        evo = {}

    _upsert_knowledge_node(
        "system:integrated-overview",
        "系统知识总览",
        "\n".join(summary_lines).strip(),
        level=1,
        parent_scope="root",
    )
    vault = export_memory_vault()
    return {
        "tree": tree_info,
        "vault": vault,
        "has_workflow": bool(workflow_dash),
        "has_evolution": bool(evo),
    }


def get_memory_dashboard() -> dict[str, Any]:
    items = list_memories(80)
    summaries = list_memory_summaries()
    if not summaries and items:
        consolidate_memories()
        summaries = list_memory_summaries()
    if items:
        tree_info = get_knowledge_tree_info()
        if not tree_info["node_count"]:
            _schedule_knowledge_tree_rebuild()
            tree_info = {**tree_info, "memory_count": len(items)}
        else:
            tree_info["memory_count"] = len(items)
    else:
        tree_info = {"node_count": 0, "category_count": 0, "memory_count": 0}

    category_counts = Counter(item["category"] for item in items)
    top_tags = Counter(tag for item in items for tag in item.get("tags", []))
    return {
        "memory_count": len(items),
        "category_counts": dict(category_counts),
        "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags.most_common(12)],
        "recent_memories": items[:20],
        "summaries": summaries,
        "knowledge_tree": tree_info,
        "vault_dir": str(VAULT_DIR),
    }


async def background_memory_maintenance(interval_sec: int = 600, startup_delay_sec: int = 30) -> None:
    import asyncio

    if startup_delay_sec > 0:
        try:
            await asyncio.sleep(startup_delay_sec)
        except asyncio.CancelledError:
            return

    while True:
        try:
            consolidate_memories()
            refresh_integrated_knowledge()
        except Exception:
            _logger.exception("background_memory_maintenance 出错，下次循环会重试")
        await asyncio.sleep(interval_sec)
