"""
agent_prompts.py — BT黑光 进化体 · 五层增强版
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

_logger = logging.getLogger(__name__)
_BACKEND = Path(__file__).parent
SOUL_PATH = _BACKEND / "SOUL.md"
USER_PATH = _BACKEND / "USER.md"
USER_PRIVATE_PATH = _BACKEND / "USER_PRIVATE.md"
_PRIVATE_UNLOCK_PHRASE = os.environ.get("BT_PRIVATE_PHRASE", "黑光深度")

_EMOTION_MAP = {
    "急躁": ["快", "赶紧", "马上", "立刻", "别废话", "直接", "现在", "催", "怎么还"],
    "专注": ["帮我", "分析", "优化", "检查", "对比", "规划", "方案", "代码"],
    "放松": ["随便", "聊聊", "说说", "怎么样", "感觉", "想想", "随意"],
    "疑惑": ["为什么", "怎么回事", "什么意思", "不懂", "解释", "搞不懂"],
    "满意": ["好的", "不错", "可以", "行", "对对对", "就这样", "完美"],
}
_EMOTION_STYLE = {
    "急躁": "极简输出，结论第一行，无废话，步骤≤3条。",
    "专注": "结构清晰，代码优先，必要时附说明。",
    "放松": "自然对话，语气轻松，可稍展开。",
    "疑惑": "先结论，再1-2句解释，可举例。",
    "满意": "简短确认，顺势推进下一步。",
    "默认": "干练，结果优先，代码优先。",
}


def _read_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def detect_emotion(text: str) -> str:
    if not text:
        return "默认"
    for emotion, keywords in _EMOTION_MAP.items():
        if any(k in text for k in keywords):
            return emotion
    if len(text) < 10:
        return "急躁"
    return "默认"


def is_private_mode(text: str) -> bool:
    return _PRIVATE_UNLOCK_PHRASE in (text or "")


def load_habit_notes(limit: int = 8) -> list:
    try:
        from memory_store import search_memories

        hits = search_memories("习惯 偏好 默认 以后都", limit=limit)
        return [h["content"] for h in hits if h.get("category") in ("preference", "playbook")]
    except Exception:
        return []


def load_recent_tasks(limit: int = 5) -> list:
    try:
        from run_graph_store import list_recent_runs

        runs = list_recent_runs(limit=limit)
        return [r.get("task") or r.get("title") or "" for r in runs if r.get("task") or r.get("title")]
    except Exception:
        pass
    try:
        from memory_store import search_memories

        hits = search_memories("项目 任务 正在做", limit=limit)
        return [h["content"] for h in hits if h.get("category") == "project"]
    except Exception:
        return []


def load_file_memories(limit: int = 4) -> list:
    try:
        from memory_store import search_memories

        hits = search_memories("文件 图片 上传 附件", limit=limit)
        results = []
        for h in hits:
            c = h.get("content", "")
            if any(k in c for k in ["文件", "图片", "上传", ".png", ".jpg", ".pdf", ".docx"]):
                results.append({"name": c[:40], "summary": c})
        return results
    except Exception:
        return []


def get_system_prompt(user_input: str = "", private_mode: bool = False) -> str:
    parts = []
    soul = _read_md(SOUL_PATH)
    if soul:
        parts.append("【人格核心·SOUL】\n" + soul)
    user_profile = _read_md(USER_PATH)
    if user_profile:
        parts.append("【用户画像】\n" + user_profile)
    emotion = detect_emotion(user_input)
    style = _EMOTION_STYLE.get(emotion, _EMOTION_STYLE["默认"])
    parts.append(f"【情绪感知】当前状态：{emotion}。回应策略：{style}")
    recent = load_recent_tasks()
    if recent:
        items = "\n".join(f"  - {t}" for t in recent[:3])
        parts.append("【主动预判】近期任务，主动衔接相关背景：\n" + items)
    habits = load_habit_notes()
    if habits:
        items = "\n".join(f"  - {h}" for h in habits[:6])
        parts.append("【习惯进化】已记录习惯，直接按此执行：\n" + items)
    files = load_file_memories()
    if files:
        lines = ["【多模态记忆】曾上传文件可直接引用："]
        for f in files[:4]:
            lines.append(f"  - {f['name']}：{f['summary'][:120]}")
        parts.append("\n".join(lines))
    if private_mode or is_private_mode(user_input):
        priv = _read_md(USER_PRIVATE_PATH)
        if priv:
            parts.append("【私密人格层·已解锁】\n" + priv)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Module-level constants expected by agent.py and tests
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_BASE: str = (
    "你是 BT黑光，一个本地优先、持久记忆的 AI Agent。\n"
    "你拥有工具调用能力，可以搜索、执行代码、操作文件、浏览网页等。\n"
    "始终优先调用工具获取真实信息，不要凭空猜测。\n"
)


def build_tools_desc() -> str:
    """Build a tools description string from the tool registry."""
    try:
        from tool_registry import TOOL_DESCRIPTIONS, all_tool_names

        names = all_tool_names()
        lines = ["\n## 可用工具"]
        for name in names:
            desc = TOOL_DESCRIPTIONS.get(name, "")
            lines.append(f"- **{name}**: {desc}")
        return "\n".join(lines)
    except Exception:
        return ""


TOOLS_DESC: str = build_tools_desc()
