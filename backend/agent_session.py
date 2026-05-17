"""Agent 会话：与 chat.db 对齐的历史与落库。"""

from __future__ import annotations

from typing import Any

from agent_runtime import get_runtime
from context_pack import compress_for_llm


def save_user_turn(session_id: str, message: str) -> None:
    from chat import save_message

    text = (message or "").strip()
    if not text:
        return
    save_message(session_id, "user", text)


def persist_agent_answer(session_id: str, steps: list[dict[str, Any]]) -> None:
    from chat import save_message

    for step in reversed(steps):
        if step.get("type") != "final_answer":
            continue
        content = (step.get("content") or "").strip()
        if content:
            save_message(session_id, "assistant", content)
        break


def build_messages_with_history(
    system_content: str,
    session_id: str,
    *,
    max_messages: int | None = None,
    max_chars: int | None = None,
) -> list[dict[str, str]]:
    from chat import get_history

    rt = get_runtime()
    limit = max_messages if max_messages is not None else rt.chat_history_max_messages
    cap = max_chars if max_chars is not None else max(2000, rt.context_block_max_chars // 2)

    history = get_history(session_id, limit=limit)
    if not history:
        return [{"role": "system", "content": system_content}]

    trimmed: list[dict[str, str]] = []
    used = 0
    for row in reversed(history):
        content = (row.get("content") or "").strip()
        if not content:
            continue
        if used + len(content) > cap and trimmed:
            break
        trimmed.insert(0, {"role": row["role"], "content": content})
        used += len(content)

    if len(trimmed) > 8:
        block = compress_for_llm(
            "\n\n".join(f"{m['role']}: {m['content']}" for m in trimmed),
            cap,
            "session_history",
        )
        if block:
            return [
                {"role": "system", "content": system_content},
                {"role": "user", "content": "## 近期会话（同 session）\n" + block},
            ]

    out: list[dict[str, str]] = [{"role": "system", "content": system_content}]
    out.extend(trimmed)
    return out
