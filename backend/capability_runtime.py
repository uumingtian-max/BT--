"""Capability runtime for BKLT 黑光.

This is the 720° execution layer: it maps high-level capabilities to concrete,
reversible tool actions. It is intentionally broad, not tied to one example.
"""

from __future__ import annotations

import json
import re
from typing import Any


def execute_runtime_capability(capability_id: str, message: str) -> dict[str, Any]:
    """Execute a high-level capability with existing tools where possible."""
    capability_id = (capability_id or "").strip()
    message = (message or "").strip()
    observations: list[dict[str, Any]] = []

    def call(tool: str, params: dict[str, Any]) -> str:
        from agent_dispatch import execute_tool_sync
        from agent_tool_map import TOOL_MAP

        if tool not in TOOL_MAP:
            raise KeyError(f"tool not found: {tool}")
        raw = execute_tool_sync(tool, params or {}, TOOL_MAP)
        observations.append({"tool": tool, "params": params, "output_preview": str(raw)[-2500:]})
        return str(raw)

    try:
        if capability_id == "project.health_check":
            target = "all" if any(k in message.lower() for k in ["all", "全部", "前端", "frontend", "构建", "build"]) else "backend"
            output = call("run_project_check", {"target": target})
            return _done(capability_id, True, f"已执行项目健康检查：{target}", observations, {"output": output})

        if capability_id == "project.self_repair_plan":
            check = call("run_project_check", {"target": "backend"})
            profile = call("get_evolution_profile", {})
            return _done(
                capability_id,
                True,
                "已检查项目状态并读取进化画像；下一步可根据失败日志生成补丁。",
                observations,
                {"check": check, "profile": profile},
            )

        if capability_id == "files.organize_workspace":
            listing = call("list_files", {"directory": "~/Desktop"})
            recent = call("get_recent_desktop_files", {"limit": 20})
            return _done(
                capability_id,
                True,
                "已扫描桌面和最近文件；当前只做扫描和整理建议，不直接移动/删除文件。",
                observations,
                {"listing": listing, "recent": recent},
            )

        if capability_id == "desktop.app_control":
            fg = call("get_foreground_window", {})
            windows = call("list_windows", {"limit": 30})
            return _done(capability_id, True, "已读取前台窗口和可见窗口列表。", observations, {"foreground": fg, "windows": windows})

        if capability_id == "browser.web_task":
            url = _first_url(message)
            if url:
                page = call("browser_navigate", {"url": url, "wait_ms": 2000, "screenshot": False})
                return _done(capability_id, True, f"已打开并读取网页：{url}", observations, {"page": page})
            search = call("web_search", {"query": message})
            return _done(capability_id, True, "未检测到 URL，已按网页研究执行搜索。", observations, {"search": search})

        if capability_id == "memory.remember_preference":
            profile = call("get_evolution_profile", {})
            return _done(
                capability_id,
                True,
                "已读取当前进化画像；长期写入偏好仍需要明确内容。",
                observations,
                {"profile": profile},
            )

        if capability_id == "skill.self_evolve":
            profile = call("get_evolution_profile", {})
            work = call("get_recent_work_summary", {})
            return _done(
                capability_id,
                True,
                "已读取进化画像和近期工作摘要，可用于生成技能改写建议。",
                observations,
                {"profile": profile, "recent_work": work},
            )

        if capability_id == "automation.flow":
            check = call("run_project_check", {"target": "backend"})
            return _done(capability_id, True, "已执行自动化可用性检查。", observations, {"check": check})

        if capability_id == "integration.external_service":
            url = _first_url(message)
            if url and message.lower().startswith(("get", "查", "读取", "请求", "访问", "打开")):
                output = call("http_request", {"url": url, "method": "GET", "timeout_sec": 20})
                return _done(capability_id, True, f"已执行外部 GET 请求：{url}", observations, {"output": output})
            return _done(capability_id, False, "外部服务能力需要明确 URL/API 和动作类型；写入型动作不会自动执行。", observations, {})

        if capability_id == "media.create_content":
            if any(k in message for k in ["图片", "画图", "生成图", "image"]):
                output = call("generate_image", {"prompt": message, "output_path": "outputs/capability_image.png"})
                return _done(capability_id, True, "已调用图片生成能力。", observations, {"output": output})
            if any(k in message for k in ["语音", "配音", "tts"]):
                output = call("text_to_speech", {"text": message, "output_path": "outputs/capability_tts.wav"})
                return _done(capability_id, True, "已调用语音生成能力。", observations, {"output": output})
            return _done(capability_id, False, "内容生成需要明确图片、视频或语音类型。", observations, {})

        if capability_id == "system.eye_comfort":
            fg = call("get_foreground_window", {})
            profile = call("get_device_profile", {})
            return _done(
                capability_id,
                True,
                "已读取当前窗口和设备画像；系统级显示动作将在通用系统动作模块接入后执行。",
                observations,
                {"foreground": fg, "profile": profile},
            )

        return _done(capability_id, False, f"能力暂未接入运行时：{capability_id}", observations, {})
    except Exception as exc:
        return _done(capability_id, False, f"能力执行失败：{exc}", observations, {"error": str(exc)})


def _done(capability_id: str, ok: bool, summary: str, observations: list[dict[str, Any]], result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": ok,
        "capability_id": capability_id,
        "summary": summary,
        "observations": observations,
        "result": result,
    }


def _first_url(text: str) -> str | None:
    match = re.search(r"https?://[^\s\]\)\}>\"']+", text or "", flags=re.I)
    return match.group(0) if match else None
