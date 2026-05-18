import json
import os
import sqlite_wal as sqlite3
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent_runtime import get_runtime
from context_pack import compress_for_llm
from llm_client import chat_stream_async
from memory_store import (
    build_memory_context,
    build_knowledge_context,
    build_playbook_context,
    consolidate_memories,
    export_memory_vault,
    get_memory_dashboard,
    list_knowledge_nodes,
    list_memories,
    list_memory_summaries,
    rebuild_knowledge_tree,
    remember_from_message,
    search_memories,
)

from skill_pack import build_skill_pack_context

router = APIRouter()
# 会话与偏好单独使用 chat.db，避免与 memory.db（长期记忆）混在同一文件
DB_PATH = os.path.join(os.path.dirname(__file__), "chat.db")
_MEMORY_LEGACY_DB = os.path.join(os.path.dirname(__file__), "memory.db")
CHAT_MESSAGE_MAX_CHARS = int(os.environ.get("CHAT_MESSAGE_MAX_CHARS", "50000"))


def _migrate_chat_from_legacy_memory(conn: sqlite3.Connection) -> None:
    """首次使用 chat.db 时，从旧版误写在 memory.db 里的会话表迁移过来。"""
    if not os.path.isfile(_MEMORY_LEGACY_DB):
        return
    if conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] > 0:
        return
    path = _MEMORY_LEGACY_DB.replace("'", "''")
    attached = False
    try:
        conn.execute(f"ATTACH DATABASE '{path}' AS mem")
        attached = True
        row = conn.execute("SELECT 1 FROM mem.sqlite_master WHERE type='table' AND name='messages'").fetchone()
        if not row:
            return
        if conn.execute("SELECT COUNT(*) FROM mem.messages").fetchone()[0] == 0:
            return
        sess = conn.execute("SELECT 1 FROM mem.sqlite_master WHERE type='table' AND name='sessions'").fetchone()
        if sess:
            conn.execute("INSERT OR REPLACE INTO sessions SELECT * FROM mem.sessions")
        conn.execute(
            """
            INSERT INTO messages (session_id, role, content, created_at)
            SELECT session_id, role, content, created_at FROM mem.messages
            """
        )
        pref = conn.execute("SELECT 1 FROM mem.sqlite_master WHERE type='table' AND name='preferences'").fetchone()
        if pref:
            conn.execute("INSERT OR REPLACE INTO preferences SELECT * FROM mem.preferences")
    except sqlite3.OperationalError:
        pass
    finally:
        if attached:
            try:
                conn.execute("DETACH DATABASE mem")
            except sqlite3.OperationalError:
                pass


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 复合索引：WHERE session_id=? ORDER BY created_at DESC 更易走索引（需 SQLite 3.30+ 支持 DESC）
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_created ON messages(session_id, created_at DESC)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    _migrate_chat_from_legacy_memory(conn)
    conn.commit()
    _init_messages_fts(conn)
    conn.close()


def _init_messages_fts(conn: sqlite3.Connection) -> None:
    """FTS5 index for cross-session chat search."""
    try:
        row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'").fetchone()
        if not row:
            conn.execute(
                """
                CREATE VIRTUAL TABLE messages_fts USING fts5(
                    content,
                    session_id UNINDEXED,
                    content='messages',
                    content_rowid='id'
                )
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS messages_fts_ai AFTER INSERT ON messages BEGIN
                  INSERT INTO messages_fts(rowid, content, session_id)
                  VALUES (new.id, new.content, new.session_id);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS messages_fts_ad AFTER DELETE ON messages BEGIN
                  INSERT INTO messages_fts(messages_fts, rowid, content, session_id)
                  VALUES ('delete', old.id, old.content, old.session_id);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS messages_fts_au AFTER UPDATE ON messages BEGIN
                  INSERT INTO messages_fts(messages_fts, rowid, content, session_id)
                  VALUES ('delete', old.id, old.content, old.session_id);
                  INSERT INTO messages_fts(rowid, content, session_id)
                  VALUES (new.id, new.content, new.session_id);
                END
                """
            )
            conn.execute(
                "INSERT INTO messages_fts(rowid, content, session_id) SELECT id, content, session_id FROM messages"
            )
            conn.commit()
    except sqlite3.OperationalError:
        pass


init_db()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: str = Field(default_factory=lambda: get_runtime().default_chat_model)
    stream: bool = True


class PreferenceUpdate(BaseModel):
    key: str
    value: str


def get_history(session_id: str, limit: int | None = None):
    if limit is None:
        limit = get_runtime().chat_history_max_messages
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


def _cap_message_content(content: str) -> str:
    text = str(content or "")
    cap = max(1000, CHAT_MESSAGE_MAX_CHARS)
    if len(text) <= cap:
        return text
    head = int(cap * 0.72)
    tail = cap - head - 80
    omitted = len(text) - head - tail
    return text[:head] + f"\n\n...[chat message truncated {omitted} chars]...\n\n" + text[-tail:]


def save_message(session_id: str, role: str, content: str):
    content = _cap_message_content(content)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content),
    )
    conn.execute(
        "INSERT OR IGNORE INTO sessions (id, title) VALUES (?, ?)",
        (session_id, content[:40]),
    )
    conn.commit()
    conn.close()


async def stream_llm(messages: list, model: str):
    async for chunk in chat_stream_async(messages, model, temperature=0.1):
        if chunk:
            yield chunk


@router.post("/")
async def chat(req: ChatRequest):
    from model_lock import enforce_locked_model

    req.model = enforce_locked_model(req.model, user_input=req.message, mode="chat")
    history = get_history(req.session_id)
    save_message(req.session_id, "user", req.message)
    remember_from_message(req.session_id, "user", req.message)
    rt = get_runtime()
    memory_context = compress_for_llm(build_memory_context(req.message), rt.context_block_max_chars, "memory")
    knowledge_context = compress_for_llm(build_knowledge_context(req.message), rt.context_block_max_chars, "knowledge")
    playbook_context = compress_for_llm(build_playbook_context(req.message), rt.context_block_max_chars, "playbook")
    skill_context = compress_for_llm(build_skill_pack_context(req.message), rt.context_block_max_chars, "skills")

    # 用户名和模型地址从环境变量 / 运行时读取，不硬编码在源码里
    _user_name = os.environ.get("AGENT_USER_NAME", "权哥").strip() or "权哥"
    _agent_name = os.environ.get("AGENT_NAME", "小涵").strip() or "小涵"
    _model_desc = ""
    if rt.llm_backend == "openai_compatible" and rt.openai_base_url:
        _model_desc = f"You run through an OpenAI-compatible backend at {rt.openai_base_url}."
    elif rt.llm_backend == "ollama":
        _model_desc = f"You run through Ollama at {rt.ollama_base}."

    guard = (
        f"You are {_agent_name}, {_user_name}'s dedicated local AI Agent running inside ONYX/ai-agent-project. "
        f"Always call the user {_user_name}. Always reply in Simplified Chinese unless {_user_name} explicitly asks for another language. "
        + (_model_desc + "\n" if _model_desc else "")
        + "Mode: this chat endpoint explains, plans, and gives operational guidance. It does not silently modify files, "
        "run tests, or change local tools unless the surrounding application/tooling explicitly performs such actions.\n"
        f"Continuity: actively use long-term memory to understand who {_user_name} is, who {_agent_name} is, the local machine state, "
        "project preferences, and ongoing work. Keep identity and context continuous across sessions.\n"
        f"Memory policy: when {_user_name} states identity, preferences, defaults, project facts, device facts, or says to remember "
        "something, treat it as long-term memory material. If memory conflicts with the current explicit instruction, "
        "follow the current instruction for this turn.\n"
        "Style: for technical issues, be rigorous, professional, concise, and practical. Say clearly when uncertain; "
        "do not fabricate facts, paths, commands, logs, or background work. Casual chat may be natural and warm, while "
        "staying within safety boundaries.\n"
        "Do not output Thinking, hidden chain-of-thought, or long internal reasoning. Output only key conclusions, "
        "necessary basis, and directly usable commands or steps.\n"
        "For important technical operations, give a short option comparison, recommended plan, and risk note. Wait for "
        f"{_user_name}'s confirmation before high-risk actions.\n"
        "Hard rules: do not invent local paths or claim you edited files unless the tool actually did it. If asked where "
        "to configure this project, point to backend/.env for LLM_BACKEND, OPENAI_BASE_URL, and model settings, then "
        "restart the backend. Keep answers short and direct."
    )
    blocks: list[str] = [guard.strip()]
    blocks.append(
        "【会话上下文】紧随本段之后的 user/assistant 消息按时间从早到晚排列；"
        "请据此理解「刚才」「上面」「之前说的」等指代。最后一条 user 是用户当前输入。"
    )
    if memory_context:
        blocks.append("【与本轮问题相关的长期记忆（仅供参考）】\n" + memory_context)
    if playbook_context:
        blocks.append("【自进化 playbook（仅供参考）】\n" + playbook_context)
    if skill_context:
        blocks.append("【技能包片段（仅供参考）】\n" + skill_context)
    if knowledge_context:
        blocks.append("【本地知识库片段（仅供参考）】\n" + knowledge_context)
    blocks.append(
        "【连贯性·最高优先级】回答必须与对话里「上下句」自然衔接、指代一致。"
        "若上方【】摘录与对话话题冲突或会打断衔接，忽略该摘录或一句话带过，禁止硬编进回答里造成跳题。"
    )
    merged_system = "\n\n---\n\n".join(blocks)
    messages = [{"role": "system", "content": merged_system}]
    messages += history + [{"role": "user", "content": req.message}]
    collected: list[str] = []

    async def generate():
        err: Optional[str] = None
        try:
            async for chunk in stream_llm(messages, req.model):
                collected.append(chunk)
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
        finally:
            final_text = "".join(collected)
            if final_text:
                stored = final_text + ("\n\n[流式输出中断: " + err + "]" if err else "")
            elif err:
                stored = f"[模型错误] {err}"
            else:
                stored = ""
            if stored:
                try:
                    save_message(req.session_id, "assistant", stored)
                    remember_from_message(req.session_id, "assistant", stored)
                except Exception:
                    pass
            yield f"data: {json.dumps({'done': True, 'error': err}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions")
def list_sessions():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "created_at": r[2]} for r in rows]


# ⚠️ /sessions/search 必须在 /sessions/{session_id}/messages 之前注册：
# FastAPI 按顺序匹配，顺序颠倒时“search”会被当作 session_id 参数，导致搜索接口永远失效。
@router.get("/sessions/search")
def search_sessions(q: str, limit: int = 20):
    """跨会话全文检索聊天内容（FTS5）。"""
    q = (q or "").strip()
    if not q:
        return {"ok": False, "error": "empty query", "hits": []}
    safe = q.replace('"', '""')
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """
            SELECT m.session_id,
                   COALESCE(s.title, '') AS title,
                   snippet(messages_fts, 0, '>>', '<<', '…', 24) AS snippet,
                   rank
            FROM messages_fts
            JOIN messages m ON m.id = messages_fts.rowid
            LEFT JOIN sessions s ON s.id = m.session_id
            WHERE messages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (f'"{safe}"', max(1, min(50, limit))),
        ).fetchall()
    except sqlite3.OperationalError as e:
        conn.close()
        return {"ok": False, "error": str(e), "hits": []}
    conn.close()
    hits = [
        {
            "session_id": r[0],
            "title": r[1],
            "snippet": r[2],
            "rank": r[3],
        }
        for r in rows
    ]
    return {"ok": True, "query": q, "hits": hits}


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    return get_history(session_id, limit=100)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/preferences")
def get_preferences():
    """长期偏好（总方案第1阶段：记住默认模型等）"""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT key, value FROM preferences").fetchall()
    conn.close()
    return {k: v for k, v in rows}


@router.post("/preferences")
def set_preference(pref: PreferenceUpdate):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO preferences (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
        (pref.key, pref.value),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/memories")
def get_memories():
    return list_memories()


@router.get("/memories/search")
def query_memories(q: str):
    return {"query": q, "items": list_memories() if not q else search_memories(q)}


@router.post("/memories/consolidate")
def consolidate_memory_now():
    return consolidate_memories()


@router.get("/memories/summaries")
def get_memory_summaries():
    return list_memory_summaries()


@router.get("/memories/dashboard")
def get_memory_dashboard_view():
    return get_memory_dashboard()


@router.post("/memories/tree/rebuild")
def rebuild_memory_tree_now():
    return rebuild_knowledge_tree()


@router.get("/memories/tree")
def get_memory_tree():
    return list_knowledge_nodes()


@router.post("/memories/vault/export")
def export_memory_vault_now():
    return export_memory_vault()
