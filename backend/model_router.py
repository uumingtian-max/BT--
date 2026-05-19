"""Smart local model routing for BKLT / 黑光 Ollama stack.

精简栈（5090 24G，各取所需）：

| 模型 | 体积 | 岗位 |
|------|------|------|
| nomic-embed-text | 0.3GB | 嵌入 / 技能检索 |
| functiongemma | 0.3GB | 工具路由（非主对话） |
| qwen3.5:4b | 3.4GB | 答案 / 视觉 / 快答 / 审查 / 结构化 |
| deepseek-r1:7b | 4.7GB | 推理 / 规划 / 进化 |
| deepseek-coder-v2:16b | 8.9GB | 复杂写码（按需加载，简单走 CODE_SIMPLE_MODEL） |

画图：generate_image（SD），不是 Ollama。
"""

from __future__ import annotations

import os
import re
from typing import Literal, TypedDict

RouterReason = Literal[
    "code",
    "code_simple",
    "reasoning",
    "structured",
    "fast",
    "agent_route",
    "default",
]

_MODEL_DEFAULTS: dict[str, str] = {
    "AGENT_DEFAULT_MODEL": "qwen3.5:4b",
    "FAST_MODEL": "qwen3.5:4b",
    "AGENT_ROUTER_MODEL": "functiongemma:latest",
    "EMBED_MODEL": "nomic-embed-text:latest",
    "REASONING_MODEL": "deepseek-r1:7b",
    "CODE_MODEL": "deepseek-coder-v2:16b",
    "CODE_SIMPLE_MODEL": "qwen3.5:4b",
    "TASK_MODEL": "qwen3.5:4b",
}


class ModelRole(TypedDict):
    env_key: str
    reason: str
    emoji: str
    label: str
    size_gb: float
    trigger: str


MODEL_ROLE_CATALOG: list[ModelRole] = [
    {
        "env_key": "EMBED_MODEL",
        "reason": "embed",
        "emoji": "📐",
        "label": "向量嵌入",
        "size_gb": 0.3,
        "trigger": "技能检索、RAG、记忆召回",
    },
    {
        "env_key": "AGENT_ROUTER_MODEL",
        "reason": "agent_route",
        "emoji": "🔧",
        "label": "工具路由",
        "size_gb": 0.3,
        "trigger": "意图解析、选工具（functiongemma）",
    },
    {
        "env_key": "FAST_MODEL",
        "reason": "fast",
        "emoji": "⚡",
        "label": "快答",
        "size_gb": 3.4,
        "trigger": "极短问候（与主聊同 qwen3.5:4b）",
    },
    {
        "env_key": "TASK_MODEL",
        "reason": "structured",
        "emoji": "📋",
        "label": "结构化",
        "size_gb": 3.4,
        "trigger": "体检报告、表单、清单",
    },
    {
        "env_key": "AGENT_DEFAULT_MODEL",
        "reason": "default",
        "emoji": "💬",
        "label": "主聊 / 视觉",
        "size_gb": 3.4,
        "trigger": "日常对话、看图",
    },
    {
        "env_key": "REASONING_MODEL",
        "reason": "reasoning",
        "emoji": "🧠",
        "label": "深度推理",
        "size_gb": 4.7,
        "trigger": "分析、规划、复杂逻辑",
    },
    {
        "env_key": "CODE_SIMPLE_MODEL",
        "reason": "code_simple",
        "emoji": "📝",
        "label": "简单代码",
        "size_gb": 3.4,
        "trigger": "短脚本、小改动",
    },
    {
        "env_key": "CODE_MODEL",
        "reason": "code",
        "emoji": "💻",
        "label": "复杂代码",
        "size_gb": 8.9,
        "trigger": "重构、多文件、架构",
    },
]

_RE_CODE = re.compile(
    r"代码|写个|写一个|实现一个|写个函数|写个脚本|写代码|编程|重构|调试|debug|bug|报错|traceback|错误堆栈|技术问题"
    r"|python|javascript|typescript|html|css|sql|bash|powershell|golang|rust|java|c\+\+"
    r"|import |def |class |async def|\.py|\.js|\.ts|\.sh|\.go|\.rs"
    r"|pip install|npm |git |dockerfile|api接口|接口文档|单元测试|lint",
    re.IGNORECASE,
)

_RE_CODE_HEAVY = re.compile(
    r"重构|架构|多文件|整个项目|全库|migrate|微服务|性能优化|并发|分布式"
    r"|refactor|monorepo|codebase|pull request|pr review",
    re.IGNORECASE,
)

_RE_REASONING = re.compile(
    r"分析|为什么|推理|逻辑|比较|权衡|规划|方案|深度|研究|推断|复杂"
    r"|pros.{0,6}cons|优缺点|利弊|综合考虑|深入|详细解释"
    r"|如何选择|应该|建议|评估|判断|架构设计|系统设计|决策",
    re.IGNORECASE,
)

_RE_STRUCTURED = re.compile(
    r"定时任务|习惯体检|体检报告|日报|周报|月报|表单|填表|报告|结构化"
    r"|整理成|归纳|列表|清单|字段|模板|格式化|cron|schedule|json格式|表格",
    re.IGNORECASE,
)

_RE_FAST = re.compile(
    r"^(你好|hi|hello|嗨|在吗|在不|好的|谢谢|thanks|ok|好|是的|明白|收到|没问题|懂了|嗯|哦)[\s!！。.?？]*$"
    r"|^帮(我|忙)[\s!！。.?？]*$"
    r"|^.{0,8}$",
    re.IGNORECASE,
)

_RE_AGENT_ROUTE = re.compile(
    r"调用工具|用哪个工具|选工具|工具路由|意图解析|判断意图"
    r"|帮我执行|用工具|搜索一下|打开网页|执行命令|运行脚本|操作浏览器",
    re.IGNORECASE,
)


def smart_router_enabled() -> bool:
    return os.environ.get("SMART_ROUTER_ENABLED", "1").strip().lower() not in (
        "0",
        "false",
        "off",
        "no",
    )


def get_model(env_key: str, fallback_key: str = "AGENT_DEFAULT_MODEL") -> str:
    value = os.environ.get(env_key, "").strip()
    if value:
        return value
    fallback = os.environ.get(fallback_key, "").strip()
    if fallback:
        return fallback
    return _MODEL_DEFAULTS.get(
        env_key,
        _MODEL_DEFAULTS.get(fallback_key, _MODEL_DEFAULTS["AGENT_DEFAULT_MODEL"]),
    )


def get_tool_router_model() -> str:
    return get_model("AGENT_ROUTER_MODEL")


def select_model(
    user_input: str,
    *,
    mode: str = "chat",
    force_model: str | None = None,
) -> tuple[str, RouterReason]:
    if force_model and force_model.strip():
        return force_model.strip(), "default"

    if not smart_router_enabled():
        return get_model("AGENT_DEFAULT_MODEL"), "default"

    text = (user_input or "").strip()

    if _RE_CODE.search(text):
        if _RE_CODE_HEAVY.search(text) or len(text) > 280:
            return get_model("CODE_MODEL"), "code"
        return get_model("CODE_SIMPLE_MODEL"), "code_simple"
    if _RE_AGENT_ROUTE.search(text):
        return get_tool_router_model(), "agent_route"
    if _RE_REASONING.search(text):
        return get_model("REASONING_MODEL"), "reasoning"
    if _RE_STRUCTURED.search(text):
        return get_model("TASK_MODEL"), "structured"
    if _RE_FAST.match(text):
        return get_model("FAST_MODEL"), "fast"
    return get_model("AGENT_DEFAULT_MODEL"), "default"


def get_embed_model() -> str:
    return get_model("EMBED_MODEL", "AGENT_DEFAULT_MODEL")


def routing_info(user_input: str = "", *, mode: str = "chat") -> dict[str, object]:
    model, reason = select_model(user_input, mode=mode)
    roles = [{**role, "model": get_model(role["env_key"])} for role in MODEL_ROLE_CATALOG]
    return {
        "model": model,
        "reason": reason,
        "mode": mode,
        "smart_router_enabled": smart_router_enabled(),
        "embed_model": get_embed_model(),
        "tool_router_model": get_tool_router_model(),
        "model_map": {
            "default": get_model("AGENT_DEFAULT_MODEL"),
            "fast": get_model("FAST_MODEL"),
            "agent_router": get_tool_router_model(),
            "embed": get_embed_model(),
            "reasoning": get_model("REASONING_MODEL"),
            "code": get_model("CODE_MODEL"),
            "code_simple": get_model("CODE_SIMPLE_MODEL"),
            "task": get_model("TASK_MODEL"),
        },
        "roles": roles,
    }
