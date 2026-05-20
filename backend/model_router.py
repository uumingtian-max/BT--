"""Smart local model routing for the ONYX Ollama stack.

模型角色与触发场景（默认 tag，可用环境变量覆盖）：

| 模型 | 体积 | 角色 | 触发场景 |
|------|------|------|----------|
| nomic-embed-text | 0.3GB | 向量嵌入 | 技能检索、RAG、记忆召回 — 全程后台 |
| functiongemma | 0.3GB | 工具路由 | Agent 判断调哪个工具、意图解析 |
| qwen3.5:0.8b | 1.0GB | 快速响应 | 纯问候 / 极短无实质内容的消息 |
| granite4:3b | 2.1GB | 结构化任务 | 定时任务、习惯体检报告、表单填写 |
| qwen3.5:4b | 3.4GB | 主聊天 | 日常对话、聊天模式默认 |
| deepseek-r1:7b | 4.7GB | 深度推理 | 分析、规划、复杂逻辑 |
| deepseek-coder-v2:16b | 8.9GB | 代码专家 | 写代码、调试、技术问题 |
"""

from __future__ import annotations

import os
import re
from typing import Literal, TypedDict

RouterReason = Literal[
    "code",
    "reasoning",
    "structured",
    "fast",
    "agent_route",
    "default",
]

_MODEL_DEFAULTS: dict[str, str] = {
    "AGENT_DEFAULT_MODEL": "qwen3.5:4b",
    "FAST_MODEL": "qwen3.5:0.8b",
    "AGENT_ROUTER_MODEL": "functiongemma:latest",
    "EMBED_MODEL": "nomic-embed-text:latest",
    "REASONING_MODEL": "deepseek-r1:7b",
    "CODE_MODEL": "deepseek-coder-v2:16b",
    "TASK_MODEL": "granite4:3b",
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
        "trigger": "技能检索、RAG、记忆召回 — 全程后台",
    },
    {
        "env_key": "AGENT_ROUTER_MODEL",
        "reason": "agent_route",
        "emoji": "🔧",
        "label": "工具路由",
        "size_gb": 0.3,
        "trigger": "Agent 判断调哪个工具、意图解析",
    },
    {
        "env_key": "FAST_MODEL",
        "reason": "fast",
        "emoji": "⚡",
        "label": "快速响应",
        "size_gb": 1.0,
        "trigger": "纯问候、无实质内容的极短句",
    },
    {
        "env_key": "TASK_MODEL",
        "reason": "structured",
        "emoji": "📋",
        "label": "结构化任务",
        "size_gb": 2.1,
        "trigger": "定时任务、习惯体检报告、表单填写",
    },
    {
        "env_key": "AGENT_DEFAULT_MODEL",
        "reason": "default",
        "emoji": "💬",
        "label": "主聊天",
        "size_gb": 3.4,
        "trigger": "日常对话、聊天模式默认",
    },
    {
        "env_key": "REASONING_MODEL",
        "reason": "reasoning",
        "emoji": "🧠",
        "label": "深度推理",
        "size_gb": 4.7,
        "trigger": "分析、规划、复杂逻辑问题",
    },
    {
        "env_key": "CODE_MODEL",
        "reason": "code",
        "emoji": "💻",
        "label": "代码专家",
        "size_gb": 8.9,
        "trigger": "写代码、调试、技术问题",
    },
]

# ---------------------------------------------------------------------------
# 正则规则
# ---------------------------------------------------------------------------

# 💻 代码专家
_RE_CODE = re.compile(
    r"代码|写个函数|写个脚本|写代码|编程|重构|调试|debug|bug|报错|traceback|错误堆栈|技术问题"
    r"|python|javascript|typescript|html|css|sql|bash|powershell|golang|rust|java|c\+\+"
    r"|import |def |class |async def|\.py|\.js|\.ts|\.sh|\.go|\.rs"
    r"|pip install|npm |git |dockerfile|api接口|接口文档|单元测试|lint",
    re.IGNORECASE,
)

# 🧠 深度推理
_RE_REASONING = re.compile(
    r"分析|为什么|推理|逻辑|比较|权衡|规划|方案|深度|研究|推断|复杂"
    r"|pros.{0,6}cons|优缺点|利弊|综合考虑|深入|详细解释|利弊分析"
    r"|如何选择|应该|建议|评估|判断|架构设计|系统设计|决策"
    r"|解释|说明|介绍|讲解|阐述|告诉我|是什么|什么是",
    re.IGNORECASE,
)

# 📋 结构化任务
_RE_STRUCTURED = re.compile(
    r"定时任务|习惯体检|体检报告|日报|周报|月报|表单|填表|报告|结构化"
    r"|整理成|归纳|列表|清单|字段|模板|格式化|整理格式|填写"
    r"|总结一下|汇总|梳理|盘点|cron|schedule|json格式|表格",
    re.IGNORECASE,
)

# 🔧 工具路由意图（functiongemma 专用，仅用于 agent 内部工具选择，不作为用户对话模型）
_RE_AGENT_ROUTE = re.compile(
    r"调用工具|用哪个工具|选工具|工具路由|意图解析|判断意图"
    r"|帮我执行|用工具|搜索一下|打开网页|执行命令|运行脚本|操作浏览器"
    r"|帮我做|帮我找|自动执行",
    re.IGNORECASE,
)

# ⚡ 快速响应 — FIX: 只匹配真正的「纯问候 / 无实质内容短句」
# 原版的 ^.{0,8}$ 会把「写代码」「解释一下」「分析一下」全部误判为 fast
# 修复：明确枚举问候词，不依赖字符数兜底
_RE_FAST = re.compile(
    r"^(你好|hi|hello|嗨|在吗|在不|好的|谢谢|thanks|thank you|ok|好|是的|明白|收到|没问题|懂了|嗯|哦|呢)[!！。.?？\s]*$"
    r"|^帮[我忙]?\s*$"
    r"|^(请问|问一下|问下|有空吗)[?？\s]*$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 「内容关键词保护」— FIX: 短句但含实质内容时，禁止降级到 fast
# 只要命中任一实质模式，即使输入极短也不走 fast 模型
# ---------------------------------------------------------------------------
_RE_HAS_SUBSTANCE = re.compile(
    r"代码|写|分析|解释|为什么|怎么|如何|帮|做|找|搜|执行|运行|调试|bug|报错"
    r"|python|js|ts|sql|git|npm|pip|docker"
    r"|规划|方案|设计|评估|比较|总结|生成|创建|修改|删除|查询",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# 公共 API（与原版签名完全兼容）
# ---------------------------------------------------------------------------


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
    """functiongemma：工具选择与意图解析（非主对话模型）。"""
    return get_model("AGENT_ROUTER_MODEL")


def select_model(
    user_input: str,
    *,
    mode: str = "chat",
    force_model: str | None = None,
) -> tuple[str, RouterReason]:
    """按用户输入选择聊天/推理模型；embed 与 tool-router 走专用 API。

    优先级（从高到低）：
      1. force_model（强制指定）
      2. smart_router 关闭 → default
      3. 代码关键词 → CODE_MODEL
      4. 推理关键词 → REASONING_MODEL          ← FIX: 调到 agent_route 前面
      5. 结构化任务 → TASK_MODEL
      6. 纯工具路由意图 → AGENT_ROUTER_MODEL   ← FIX: 降低优先级，避免截断推理
      7. 纯问候（经实质内容保护后）→ FAST_MODEL
      8. 兜底 → AGENT_DEFAULT_MODEL
    """
    if force_model and force_model.strip():
        return force_model.strip(), "default"

    if not smart_router_enabled():
        return get_model("AGENT_DEFAULT_MODEL"), "default"

    text = (user_input or "").strip()

    # 1. 代码 — 最高优先，无论长短
    if _RE_CODE.search(text):
        return get_model("CODE_MODEL"), "code"

    # 2. 深度推理 — FIX: 提前到 agent_route 之前
    #    原版「帮我找一下架构方案」会先命中 agent_route（帮我找），
    #    现在推理先判断，避免高质量任务被降级到 functiongemma
    if _RE_REASONING.search(text):
        return get_model("REASONING_MODEL"), "reasoning"

    # 3. 结构化任务
    if _RE_STRUCTURED.search(text):
        return get_model("TASK_MODEL"), "structured"

    # 4. 工具路由意图（仅用于 agent 内部调度，不做通用对话兜底）
    if _RE_AGENT_ROUTE.search(text):
        return get_tool_router_model(), "agent_route"

    # 5. 纯问候 / 无实质内容（_RE_FAST 已枚举具体句式，不再用 HAS_SUBSTANCE 二次拦截）
    if _RE_FAST.match(text):
        return get_model("FAST_MODEL"), "fast"

    # 6. 兜底：主聊天模型
    return get_model("AGENT_DEFAULT_MODEL"), "default"


def get_embed_model() -> str:
    return get_model("EMBED_MODEL", "AGENT_DEFAULT_MODEL")


def routing_info(user_input: str = "", *, mode: str = "chat") -> dict[str, object]:
    model, reason = select_model(user_input, mode=mode)
    roles = [
        {
            **role,
            "model": get_model(role["env_key"]),
        }
        for role in MODEL_ROLE_CATALOG
    ]
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
            "task": get_model("TASK_MODEL"),
        },
        "roles": roles,
    }
