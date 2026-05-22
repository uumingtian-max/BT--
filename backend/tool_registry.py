"""Structured metadata for Agent tools.

This module is intentionally lightweight and import-safe: it does not import the
actual tool handlers.  It can therefore be used by tests, documentation helpers,
and future UI endpoints without triggering heavy runtime dependencies.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal, TypedDict

RiskLevel = Literal["safe", "confirm", "dangerous"]


class ToolMetadata(TypedDict):
    name: str
    group: str
    description: str
    risk_level: RiskLevel
    timeout_seconds: int
    input_schema: dict[str, Any]
    enabled: bool


TOOL_GROUPS: dict[str, list[str]] = {
    "capability_control": ["route_capability_intent", "execute_capability"],
    "search_crawl": ["web_search", "local_search", "local_scrape_url"],
    "files_code": ["read_file", "write_file", "list_files", "execute_python", "run_shell"],
    "system_info": [
        "get_system_info",
        "get_gpu_status",
        "optimize_gpu_memory",
        "get_process_list",
        "kill_process",
        "get_network_status",
    ],
    "files_enhanced": ["search_files"],
    "profile_orchestrate": [
        "get_device_profile",
        "get_recent_desktop_files",
        "get_recent_work_summary",
        "get_evolution_profile",
        "run_task_orchestration",
    ],
    "knowledge_media": [
        "notebook_ingest",
        "notebook_synthesize",
        "generate_image",
        "generate_video",
        "generate_ai_video",
        "text_to_speech",
        "run_project_check",
    ],
    "desktop_control": [
        "open_url",
        "open_path",
        "get_foreground_window",
        "list_windows",
        "focus_window",
        "send_hotkey",
        "type_text",
        "click_screen",
    ],
    "browser_automation": [
        "browser_navigate",
        "browser_playwright",
        "browser_screenshot",
        "browser_click_and_extract",
        "browser_fill_form",
    ],
    "parallel": ["run_parallel_subagents"],
    "integration": ["http_request", "query_database", "mcp_invoke"],
}

TOOL_DESCRIPTIONS: dict[str, str] = {
    "route_capability_intent": "仅做能力意图分类与计划预览，不执行。用户要做事时用 execute_capability 或具体工具。",
    "execute_capability": "根据用户意图自动匹配高层能力并立即执行（项目检查、桌面扫描、浏览器等）。",
    "run_shell": "在本机项目目录执行 PowerShell/cmd 命令（git、pytest、npm、构建等），返回真实输出。",
    "web_search": "联网搜索最新信息。",
    "local_search": "使用本地无 Key 搜索，并可抓取搜索结果正文。",
    "local_scrape_url": "抓取指定网页并提取可读 Markdown 文本。",
    "read_file": "读取本地文件内容。",
    "write_file": "写入或创建本地文件。",
    "list_files": "列出目录内容。",
    "execute_python": "执行 Python 代码。",
    "get_system_info": (
        "检测本机硬件信息：CPU 型号/核心数、GPU 型号/显存、内存、磁盘、系统版本。"
        "用户问电脑配置、硬件参数、显卡型号、内存大小时必须调用，禁止猜测。"
    ),
    "get_gpu_status": (
        "获取 GPU 实时状态：利用率、显存占用、温度、功耗（nvidia-smi）。"
        "用户问显存占用、GPU 负载、温度、5090 状态时必须调用。"
    ),
    "optimize_gpu_memory": "清理 GPU 显存缓存（torch.cuda.empty_cache），释放未用 CUDA 内存。",
    "get_process_list": "获取系统进程列表，按 CPU 或内存占用排序。",
    "kill_process": "结束指定进程（需 pid 或进程名）。高风险，需用户确认。",
    "get_network_status": "网络 IO 统计、网卡地址、连接与端口占用（可筛指定端口）。",
    "search_files": "在桌面/文档/下载/项目目录按文件名或扩展名搜索，非全盘扫描。",
    "get_device_profile": "读取本机设备画像与使用习惯摘要。",
    "get_recent_desktop_files": "读取最近有变化的桌面文件。",
    "get_recent_work_summary": "综合设备画像与最近桌面文件，总结最近工作内容。",
    "get_evolution_profile": "读取自进化画像摘要。",
    "run_task_orchestration": "执行多模型协作规划、实现、审查和汇总。",
    "notebook_ingest": "把长文本笔记写入本地知识库。",
    "notebook_synthesize": "用模型整理长材料后写入知识库。",
    "generate_image": "本地文生图。",
    "generate_video": "生成视频：image_paths=多图时真实合成 mp4；仅 prompt 时多为占位动画（非 LongLive/Wan，除非已接 VIDEO_GEN_BACKEND）。",
    "generate_ai_video": "文生视频别名；同 generate_video，勿声称已接 LongLive。",
    "text_to_speech": "本地文字转语音 wav。",
    "run_project_check": "运行项目内置检查。",
    "open_url": "在默认浏览器打开网页。",
    "open_path": "打开本地文件、文件夹或程序。",
    "get_foreground_window": "读取当前 Windows 前台窗口标题。",
    "list_windows": "列出当前可见窗口。",
    "focus_window": "按窗口标题关键字聚焦第三方 App。",
    "send_hotkey": "向当前前台窗口发送快捷键。",
    "type_text": "向当前前台窗口输入文字。",
    "click_screen": "点击屏幕坐标。",
    "browser_navigate": "用 Playwright 打开网页并提取正文。",
    "browser_playwright": "执行通用 Playwright 浏览器动作。",
    "browser_screenshot": "网页全页截图。",
    "browser_click_and_extract": "打开网页、点击元素并提取内容。",
    "browser_fill_form": "填写并提交网页表单。",
    "run_parallel_subagents": "并行执行多条子提示并汇总。",
    "http_request": "发送 HTTP 请求。",
    "query_database": "查询 SQLite 数据库。",
    "mcp_invoke": "调用 MCP 工具。",
}

TOOL_RISK_LEVELS: dict[str, RiskLevel] = {
    "route_capability_intent": "safe",
    "execute_capability": "safe",
    "run_shell": "confirm",
    "web_search": "safe",
    "local_search": "safe",
    "local_scrape_url": "safe",
    "read_file": "safe",
    "write_file": "confirm",
    "list_files": "safe",
    "execute_python": "dangerous",
    "get_system_info": "safe",
    "get_gpu_status": "safe",
    "optimize_gpu_memory": "confirm",
    "get_process_list": "safe",
    "kill_process": "dangerous",
    "get_network_status": "safe",
    "search_files": "safe",
    "get_device_profile": "safe",
    "get_recent_desktop_files": "safe",
    "get_recent_work_summary": "safe",
    "get_evolution_profile": "safe",
    "run_task_orchestration": "safe",
    "notebook_ingest": "confirm",
    "notebook_synthesize": "confirm",
    "generate_image": "confirm",
    "generate_video": "confirm",
    "generate_ai_video": "confirm",
    "text_to_speech": "confirm",
    "run_project_check": "safe",
    "open_url": "confirm",
    "open_path": "confirm",
    "get_foreground_window": "safe",
    "list_windows": "safe",
    "focus_window": "confirm",
    "send_hotkey": "dangerous",
    "type_text": "dangerous",
    "click_screen": "dangerous",
    "browser_navigate": "confirm",
    "browser_playwright": "dangerous",
    "browser_screenshot": "confirm",
    "browser_click_and_extract": "dangerous",
    "browser_fill_form": "dangerous",
    "run_parallel_subagents": "safe",
    "http_request": "confirm",
    "query_database": "dangerous",
    "mcp_invoke": "dangerous",
}

_DEFAULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": True,
}

TOOL_INPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "route_capability_intent": {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "max_matches": {"type": "integer", "minimum": 1, "maximum": 8},
        },
        "required": ["message"],
    },
    "web_search": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
    "local_search": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            "scrape": {"type": "boolean"},
        },
        "required": ["query"],
    },
    "local_scrape_url": {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
    "read_file": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
    "write_file": {
        "type": "object",
        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"],
    },
    "list_files": {"type": "object", "properties": {"directory": {"type": "string"}}},
    "execute_python": {
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"],
    },
    "run_shell": {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "cwd": {"type": "string", "description": "project | desktop | home | path"},
            "shell": {"type": "string", "enum": ["powershell", "cmd"]},
        },
        "required": ["command"],
    },
    "execute_capability": {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    },
    "get_gpu_status": _DEFAULT_SCHEMA,
    "optimize_gpu_memory": _DEFAULT_SCHEMA,
    "get_process_list": {
        "type": "object",
        "properties": {
            "top_n": {"type": "integer", "minimum": 1, "maximum": 50},
            "sort_by": {"type": "string", "enum": ["cpu", "memory"]},
        },
    },
    "kill_process": {
        "type": "object",
        "properties": {
            "pid": {"type": "integer"},
            "name": {"type": "string"},
            "force": {"type": "boolean"},
        },
    },
    "get_network_status": {
        "type": "object",
        "properties": {
            "include_connections": {"type": "boolean"},
            "port": {"type": "integer"},
        },
    },
    "search_files": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "directory": {"type": "string"},
            "extension": {"type": "string"},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 80},
            "regex": {"type": "boolean"},
            "modified_within_hours": {"type": "number"},
        },
    },
    "run_task_orchestration": {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    },
    "notebook_ingest": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "text": {"type": "string"}},
        "required": ["text"],
    },
    "notebook_synthesize": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "text": {"type": "string"}},
        "required": ["text"],
    },
    "generate_image": {
        "type": "object",
        "properties": {"prompt": {"type": "string"}, "output_path": {"type": "string"}},
        "required": ["prompt"],
    },
    "generate_video": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "image_paths": {"type": "array", "items": {"type": "string"}},
            "output_path": {"type": "string"},
            "fps": {"type": "number"},
        },
    },
    "generate_ai_video": {
        "type": "object",
        "properties": {"prompt": {"type": "string"}},
        "required": ["prompt"],
    },
    "text_to_speech": {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
    "run_project_check": {
        "type": "object",
        "properties": {"target": {"enum": ["backend", "frontend", "all"]}},
    },
    "open_url": {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
    "open_path": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
    "focus_window": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
    },
    "send_hotkey": {
        "type": "object",
        "properties": {"keys": {"type": "string"}},
        "required": ["keys"],
    },
    "type_text": {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
    "click_screen": {
        "type": "object",
        "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
        "required": ["x", "y"],
    },
    "browser_navigate": {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
    "browser_playwright": {
        "type": "object",
        "properties": {"url": {"type": "string"}, "action": {"type": "string"}},
    },
    "browser_screenshot": {
        "type": "object",
        "properties": {"url": {"type": "string"}, "output_path": {"type": "string"}},
        "required": ["url"],
    },
    "browser_click_and_extract": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "selector": {"type": "string"},
            "extract_selector": {"type": "string"},
        },
        "required": ["url", "selector"],
    },
    "browser_fill_form": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "fields": {"type": "object"},
            "submit_selector": {"type": "string"},
        },
        "required": ["url", "fields"],
    },
    "run_parallel_subagents": {
        "type": "object",
        "properties": {"tasks": {"type": "array", "items": {"type": "string"}}},
        "required": ["tasks"],
    },
    "http_request": {
        "type": "object",
        "properties": {"url": {"type": "string"}, "method": {"type": "string"}},
        "required": ["url"],
    },
    "query_database": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "sql": {"type": "string"},
            "limit": {"type": "integer"},
        },
        "required": ["sql"],
    },
    "mcp_invoke": {
        "type": "object",
        "properties": {
            "server": {"type": "string"},
            "tool": {"type": "string"},
            "arguments": {"type": "object"},
        },
        "required": ["tool"],
    },
}


def all_tool_names() -> list[str]:
    """Return all registered tool names in stable display order (deduped)."""
    names: list[str] = []
    seen: set[str] = set()
    for group_names in TOOL_GROUPS.values():
        for name in group_names:
            if name in seen:
                continue
            seen.add(name)
            names.append(name)
    return names


def _group_for_tool(name: str) -> str:
    for group, names in TOOL_GROUPS.items():
        if name in names:
            return group
    raise KeyError(f"Tool is not assigned to a group: {name}")


def get_tool_metadata(name: str) -> ToolMetadata:
    """Return one tool's structured metadata."""
    if name not in TOOL_DESCRIPTIONS:
        raise KeyError(f"Unknown tool metadata: {name}")
    return {
        "name": name,
        "group": _group_for_tool(name),
        "description": TOOL_DESCRIPTIONS[name],
        "risk_level": TOOL_RISK_LEVELS[name],
        "timeout_seconds": 30,
        "input_schema": deepcopy(TOOL_INPUT_SCHEMAS.get(name, _DEFAULT_SCHEMA)),
        "enabled": True,
    }


def list_tool_metadata() -> list[ToolMetadata]:
    """Return structured metadata for every registered Agent tool."""
    return [get_tool_metadata(name) for name in all_tool_names()]


def validate_tool_registry() -> list[str]:
    """Return human-readable registry problems; empty means healthy."""
    problems: list[str] = []
    names = all_tool_names()
    if len(names) != len(set(names)):
        problems.append("TOOL_GROUPS contains duplicate tool names")
    for name in names:
        if name not in TOOL_DESCRIPTIONS:
            problems.append(f"{name} is missing description")
        if name not in TOOL_RISK_LEVELS:
            problems.append(f"{name} is missing risk level")
        elif TOOL_RISK_LEVELS[name] not in {"safe", "confirm", "dangerous"}:
            problems.append(f"{name} has invalid risk level: {TOOL_RISK_LEVELS[name]}")
    for table_name, table in {
        "TOOL_DESCRIPTIONS": TOOL_DESCRIPTIONS,
        "TOOL_RISK_LEVELS": TOOL_RISK_LEVELS,
        "TOOL_INPUT_SCHEMAS": TOOL_INPUT_SCHEMAS,
    }.items():
        for name in table:
            if name not in names:
                problems.append(f"{table_name} contains unknown tool: {name}")
    return problems


def get_full_registry() -> dict[str, Any]:
    """给前端用的完整工具信息 + risk_summary。"""
    tools = list_tool_metadata()
    return {
        "tools": tools,
        "groups": TOOL_GROUPS,
        "risk_summary": {
            "safe": len([t for t in tools if t.get("risk_level") == "safe"]),
            "confirm": len([t for t in tools if t.get("risk_level") == "confirm"]),
            "dangerous": len([t for t in tools if t.get("risk_level") == "dangerous"]),
        },
    }
