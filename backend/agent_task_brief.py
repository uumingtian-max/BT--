"""Build a visible task plan before Agent executes tools (Hermes-style workbench)."""

from __future__ import annotations

import re
from typing import Any

_TOOL_TITLES: dict[str, str] = {
    "run_project_check": "检查项目依赖与构建",
    "local_scrape_url": "抓取网页并提取要点",
    "local_search": "联网搜索并可选抓取",
    "read_file": "读取本地文件",
    "list_files": "列出目录文件",
    "write_file": "写入本地文件",
    "execute_python": "执行 Python 代码",
    "run_task_orchestration": "多模型协作（规划→编码→审查）",
    "get_device_profile": "采集设备与工作画像",
    "browser_navigate": "浏览器打开页面",
    "browser_screenshot": "网页截图",
    "generate_image": "生成图片",
    "generate_video": "生成视频",
    "text_to_speech": "文字转语音",
    "notebook_ingest": "写入知识库",
    "open_url": "打开链接",
}


def _summarize_goal(message: str) -> str:
    text = message.strip()
    if len(text) <= 120:
        return text
    return text[:117] + "…"


def _tool_step_title(tool: str, params: dict[str, Any]) -> str:
    base = _TOOL_TITLES.get(tool, tool)
    if tool == "run_project_check":
        target = str(params.get("target") or "all")
        if target == "backend":
            return "检查 backend 依赖与语法"
        if target == "frontend":
            return "检查 frontend 构建"
        return base
    if tool == "local_scrape_url":
        url = str(params.get("url") or "")
        if url:
            return f"抓取网页：{url}"
    if tool == "local_search":
        q = str(params.get("query") or "")[:60]
        return f"搜索：{q}" if q else base
    if tool == "read_file":
        path = str(params.get("path") or "")[-40:]
        return f"读取文件 …{path}" if path else base
    return base


def _looks_like_orchestration(message: str) -> bool:
    text = message.strip()
    lower = text.lower()
    markers = ["多模型", "编排", "协作完成", "完整项目", "任务分解", "orchestrate"]
    return any(k in text or k in lower for k in markers) and len(text) > 40


def _planned_steps(message: str) -> list[dict[str, Any]]:
    # Local import avoids circular import at module load.
    from agent import infer_tool_from_message

    steps: list[dict[str, Any]] = []
    primary = infer_tool_from_message(message)
    if primary and primary.get("name"):
        tool = str(primary["name"])
        params: dict[str, Any] = dict(primary.get("parameters") or {})
        steps.append(
            {
                "id": "1",
                "title": _tool_step_title(tool, params),
                "tool": tool,
                "status": "pending",
            }
        )
        return steps

    if _looks_like_orchestration(message):
        return [
            {
                "id": "1",
                "title": _TOOL_TITLES["run_task_orchestration"],
                "tool": "run_task_orchestration",
                "status": "pending",
            }
        ]

    return [
        {
            "id": "1",
            "title": "理解任务并选择合适工具",
            "tool": None,
            "status": "pending",
        }
    ]


def build_task_plan(message: str) -> dict[str, Any]:
    steps = _planned_steps(message)
    goal = _summarize_goal(message)
    tools = [s["tool"] for s in steps if s.get("tool")]
    if tools:
        summary = f"将按 {len(steps)} 步执行：{' → '.join(tools)}"
    else:
        summary = "先理解你的目标，再决定是否调用工具。"
    return {
        "goal": goal,
        "summary": summary,
        "steps": steps,
    }


def plan_progress_from_steps(plan: dict[str, Any], agent_steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge run progress into a task plan for the UI."""
    import copy

    merged = copy.deepcopy(plan)
    called = {s.get("tool") for s in agent_steps if s.get("type") == "tool_call"}
    finished = {s.get("tool") for s in agent_steps if s.get("type") == "tool_result"}
    failed_tools = set()
    for s in agent_steps:
        if s.get("type") != "tool_result":
            continue
        raw = str(s.get("result") or "").lower()
        if "error" in raw or "失败" in raw:
            failed_tools.add(s.get("tool"))

    for step in merged.get("steps") or []:
        tool = step.get("tool")
        if not tool:
            if agent_steps and any(x.get("type") == "tool_call" for x in agent_steps):
                step["status"] = "done"
            continue
        if tool in failed_tools:
            step["status"] = "failed"
        elif tool in finished:
            step["status"] = "done"
        elif tool in called:
            step["status"] = "running"
        else:
            step["status"] = "pending"
    return merged
