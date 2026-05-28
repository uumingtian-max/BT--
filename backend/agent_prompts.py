"""
agent_prompts.py — BT黑光 进化体 · 五层增强版
新增能力：
  1. 情绪感知    — 识别用户语气，动态调整回应密度/节奏
  2. 主动预判    — 注入近期任务上下文，对话开头主动提示
  3. 习惯进化    — 读取 USER.md/SOUL.md/习惯记忆，行为贴合权哥
  4. 多模态记忆  — 附件/图片/文件内容自动摘要存记忆，下次引用
  5. 私密人格层  — 口令解锁深度模式，风格彻底切换
"""
from __future__ import annotations

import os
import re
import json
import logging
from pathlib import Path
from typing import Any

_logger = logging.getLogger(__name__)

# ── 路径 ──────────────────────────────────────────────────────
_BACKEND = Path(__file__).parent
SOUL_PATH         = _BACKEND / "SOUL.md"
USER_PATH         = _BACKEND / "USER.md"
USER_PRIVATE_PATH = _BACKEND / "USER_PRIVATE.md"

# ── 私密模式口令（可在 .env 里改）────────────────────────────
_PRIVATE_UNLOCK_PHRASE = os.environ.get("BT_PRIVATE_PHRASE", "黑光深度")

# ── 情绪关键词映射 ────────────────────────────────────────────
_EMOTION_MAP = {
    "急躁": ["快", "赶紧", "马上", "立刻", "别废话", "直接", "现在", "催", "怎么还"],
    "专注": ["帮我", "分析", "优化", "检查", "对比", "规划", "方案", "代码"],
    "放松": ["随便", "聊聊", "说说", "怎么样", "感觉", "想想", "随意"],
    "疑惑": ["为什么", "怎么回事", "什么意思", "不懂", "解释", "搞不懂"],
    "满意": ["好的", "不错", "可以", "行", "对对对", "就这样", "完美"],
}

_EMOTION_STYLE = {
    "急躁": "极简输出，结论第一行，无废话，步骤≤3条。",
    "专注": "结构清晰，代码优先，必要时附说明，不超过需要的长度。",
    "放松": "自然对话，可以稍展开，语气轻松，偶尔可以有一句话的闲聊。",
    "疑惑": "先给结论，再用1-2句解释，可以举一个具体例子。",
    "满意": "简短确认，顺势推进下一步，不重复已说的内容。",
    "默认": "干练，结果优先，代码优先，不列无意义选项。",
}


# ── 工具函数 ──────────────────────────────────────────────────
def _read_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def detect_emotion(text: str) -> str:
    """从用户输入文本中检测情绪状态，返回情绪标签。"""
    if not text:
        return "默认"
    for emotion, keywords in _EMOTION_MAP.items():
        if any(k in text for k in keywords):
            return emotion
    # 短句 + 无标点 → 急躁信号
    if len(text) < 10 and "？" not in text and "。" not in text:
        return "急躁"
    return "默认"


def is_private_mode(text: str) -> bool:
    """检测用户输入是否包含私密模式解锁口令。"""
    return _PRIVATE_UNLOCK_PHRASE in (text or "")


def _build_emotion_block(emotion: str) -> str:
    style = _EMOTION_STYLE.get(emotion, _EMOTION_STYLE["默认"])
    return f"【情绪感知】当前用户状态：{emotion}。回应策略：{style}"


def _build_proactive_block(recent_tasks: list[str]) -> str:
    """根据近期任务生成主动预判提示。"""
    if not recent_tasks:
        return ""
    top = recent_tasks[:3]
    items = "\n".join(f"  - {t}" for t in top)
    return (
        "【主动预判】根据权哥近期任务，本轮对话开头可主动提示相关进展或待办：\n"
        f"{items}\n"
        "如果当前问题与上述任务相关，主动衔接而不是等用户重新说明背景。"
    )


def _build_habit_block(habit_notes: list[str]) -> str:
    """注入习惯进化记录。"""
    if not habit_notes:
        return ""
    items = "\n".join(f"  - {h}" for h in habit_notes[:6])
    return (
        "【习惯进化】已记录的权哥操作习惯（直接按此方式执行，无需再问）：\n"
        f"{items}"
    )


def _build_multimodal_memory_block(file_memories: list[dict]) -> str:
    """注入多模态文件记忆摘要。"""
    if not file_memories:
        return ""
    lines = ["【多模态记忆】权哥曾上传/引用过的文件（可直接引用无需重新上传）："]
    for fm in file_memories[:4]:
        name    = fm.get("name", "未知文件")
        summary = fm.get("summary", "")[:120]
        lines.append(f"  - {name}：{summary}")
    return "\n".join(lines)


def _build_private_block(user_private_md: str) -> str:
    """私密人格层内容注入。"""
    if not user_private_md:
        return ""
    return (
        "【私密人格层·已解锁】\n"
        "以下是权哥的私密设定，本轮对话完全按此风格，覆盖默认设定：\n"
        f"{user_private_md}"
    )


# ── 主Prompt构建 ──────────────────────────────────────────────
_AGENT_PROMPT_BASE = (
    "你是一个本地 AI Agent，能听懂、能分析、能真正在本机执行。"
    "你的职责是**做完事**，不是给教程、不是列 A/B/C 选项、不是让用户自己去点。"
    "当需要读取文件、列目录、搜索、执行 shell/git、执行 Python、查看设备画像、"
    "编排多模型任务、写入知识库、本地画图/视频/语音时，必须自己调用对应工具。\n"
    "若用户意图明确（例如 git status、跑 pytest、列出桌面文件），第一轮就必须 <tool_call>，"
    "禁止先输出长篇分析再询问要不要做。\n"
    "若用户提到「编排」「多模型」「复杂方案对比」「协作审查」等，应优先使用 run_task_orchestration，"
    "并把用户整句需求作为 parameters.message 传入。\n\n"
    "能力边界要准确表达：当前已能联网搜索、本地网页抓取、文件管理、代码执行、设备画像、"
    "知识库、多模型编排、图像/视频/语音生成、项目检查和 Windows 第三方 App 基础控制。\n"
    "视频分两类：**理解**（用户上传附件 → API attachments 多模态；vLLM :8001 未就绪须报错，"
    "禁止根据路径瞎猜）与 **生成**（generate_video：多图→真实 mp4；"
    "仅 prompt→多为占位动画，不是 LongLive/Wan，除非维护者已接后端）。不要混为一谈。\n"
    "生成图片/视频后，最终回答里必须写出 outputs 下的文件路径，便于界面预览。\n"
    "文生视频优先 generate_video(prompt=...)；有多张图时用 image_paths 合成幻灯片。\n"
    "第三方 App 控制可列窗口、聚焦窗口、发送快捷键、输入文字、坐标点击；"
    "需要用户明确目标窗口/快捷键/坐标，不能声称已具备越权控制或绕过安全限制。\n\n"
)


def build_system_prompt(
    user_input: str = "",
    recent_tasks: list[str] | None = None,
    habit_notes: list[str] | None = None,
    file_memories: list[dict] | None = None,
    private_mode: bool = False,
) -> str:
    """
    构建完整 system prompt，自动集成五层增强。

    参数：
        user_input    : 当前用户输入（用于情绪检测和私密模式检测）
        recent_tasks  : 近期任务列表（从 run_graph / memory 中取）
        habit_notes   : 习惯记录列表（从 memory_store 中取）
        file_memories : 多模态文件记忆列表 [{name, summary}]
        private_mode  : 是否已解锁私密模式（由调用方维护session状态）
    """
    parts: list[str] = []

    # 1. 基础 Agent 能力定义
    parts.append(_AGENT_PROMPT_BASE.strip())

    # 2. SOUL — 人格核心
    soul = _read_md(SOUL_PATH)
    if soul:
        parts.append("【人格核心·SOUL】\n" + soul)

    # 3. USER — 用户画像
    user_profile = _read_md(USER_PATH)
    if user_profile:
        parts.append("【用户画像】\n" + user_profile)

    # 4. 情绪感知
    emotion = detect_emotion(user_input)
    parts.append(_build_emotion_block(emotion))

    # 5. 主动预判
    if recent_tasks:
        proactive = _build_proactive_block(recent_tasks)
        if proactive:
            parts.append(proactive)

    # 6. 习惯进化
    if habit_notes:
        habit = _build_habit_block(habit_notes)
        if habit:
            parts.append(habit)

    # 7. 多模态记忆
    if file_memories:
        mm = _build_multimodal_memory_block(file_memories)
        if mm:
            parts.append(mm)

    # 8. 私密人格层
    if private_mode or is_private_mode(user_input):
        private_md = _read_md(USER_PRIVATE_PATH)
        priv = _build_private_block(private_md)
        if priv:
            parts.append(priv)

    return "\n\n".join(parts)


# ── 从 memory_store 拉取习惯和近期任务的辅助函数 ──────────────
def load_habit_notes(limit: int = 8) -> list[str]:
    """从 memory_store 拉取习惯类记忆。"""
    try:
        from memory_store import search_memories
        hits = search_memories("习惯 偏好 默认 以后都", limit=limit)
        return [h["content"] for h in hits if h.get("category") in ("preference", "playbook")]
    except Exception:
        return []


def load_recent_tasks(limit: int = 5) -> list[str]:
    """从 run_graph_store 拉取近期任务摘要。"""
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


def load_file_memories(limit: int = 4) -> list[dict]:
    """从 memory_store 拉取文件类记忆。"""
    try:
        from memory_store import search_memories
        hits = search_memories("文件 图片 上传 附件", limit=limit)
        results = []
        for h in hits:
            content = h.get("content", "")
            if any(k in content for k in ["文件", "图片", "上传", ".png", ".jpg", ".pdf", ".docx"]):
                results.append({"name": content[:40], "summary": content})
        return results
    except Exception:
        return []


# ── 对外统一入口（chat.py / agent.py 直接调这一个）────────────
def get_system_prompt(user_input: str = "", private_mode: bool = False) -> str:
    """
    chat.py 和 agent.py 调用的统一入口。
    自动拉取记忆、任务、习惯，构建完整 system prompt。
    """
    recent_tasks  = load_recent_tasks()
    habit_notes   = load_habit_notes()
    file_memories = load_file_memories()

    return build_system_prompt(
        user_input    = user_input,
        recent_tasks  = recent_tasks,
        habit_notes   = habit_notes,
        file_memories = file_memories,
        private_mode  = private_mode,
    )


# ── 向后兼容：agent.py 依赖的导出 ────────────────────────────
from tool_registry import TOOL_DESCRIPTIONS, all_tool_names

def _build_tools_desc() -> str:
    """从 tool_registry 生成工具描述文本。"""
    lines = ["\n## 可用工具\n"]
    for name in sorted(all_tool_names()):
        desc = TOOL_DESCRIPTIONS.get(name, "")
        if desc:
            lines.append(f"- {name}：{desc}")
    lines.append("\n工具调用格式必须严格输出：")
    lines.append('<tool_call>{"name":"tool_name","parameters":{"key":"value"}}</tool_call>')
    return "\n".join(lines)

TOOLS_DESC = _build_tools_desc()
SYSTEM_PROMPT_BASE = _AGENT_PROMPT_BASE

print("agent_prompts.py ready for write")
