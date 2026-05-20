"""Agent tool handlers and TOOL_MAP (registry metadata lives in tool_registry)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.search import web_search
from tools.local_crawl import local_scrape_url, local_search
from tools.file_ops import read_file, write_file, list_files
from tools.http_tool import http_request
from tools.db_query import query_database
from tools.mcp_invoke import mcp_invoke
from tools.system_info import get_system_info
from tools.gpu_monitor import get_gpu_status, optimize_gpu_memory
from tools.process_info import get_process_list, kill_process
from tools.network_info import get_network_status
from tools.search_files import search_files
from subagent_runner import run_parallel_subagents_sync
from orchestrator import run_orchestration
from memory_store import ingest_notebook_corpus
from observe import get_evolution_profile_text
from agent_runtime import get_runtime, orchestration_defaults
from llm_client import chat_complete_sync


def _device_profile_tool(_: dict) -> str:
    try:
        from observe import format_profile_for_llm

        return format_profile_for_llm()
    except Exception as e:
        return f"get_device_profile error: {e}"


def _recent_desktop_files_tool(params: dict) -> str:
    try:
        from observe import desktop_recent_files

        limit = int(params.get("limit", 12))
        rows = desktop_recent_files(limit)
        if not rows:
            return "最近没有采集到桌面文件变化。"
        lines = ["最近桌面文件："]
        for row in rows[:limit]:
            lines.append(f"- {row.get('name', '?')} | {row.get('path', '')}")
        return "\n".join(lines)
    except Exception as e:
        return f"get_recent_desktop_files error: {e}"


def _recent_work_summary_tool(_: dict) -> str:
    try:
        from observe import format_profile_for_llm, desktop_recent_files

        profile_text = format_profile_for_llm()
        recent_files = desktop_recent_files(12)
        lines = ["## 最近活动总结素材", profile_text.strip(), "", "## 最近桌面文件"]
        if recent_files:
            for row in recent_files:
                lines.append(f"- {row.get('name', '?')} | {row.get('path', '')}")
        else:
            lines.append("- 最近没有采集到桌面文件变化。")
        lines.append("")
        lines.append("请基于这些素材，用中文直接总结用户最近主要在做什么，给出 3-6 条简洁判断，不要解释工具。")
        return "\n".join(lines)
    except Exception as e:
        return f"get_recent_work_summary error: {e}"


def _evolution_profile_tool(_: dict) -> str:
    try:
        return get_evolution_profile_text()
    except Exception as e:
        return f"get_evolution_profile error: {e}"


def _execute_capability_tool(params: dict) -> str:
    try:
        from intent_router import route_intent
        from capability_runtime import execute_runtime_capability

        message = params.get("message") or params.get("text") or params.get("query") or ""
        message = str(message).strip()
        if not message:
            return "execute_capability error: missing message"
        route = route_intent(message, max_matches=3)
        matches = route.get("matches") or []
        if not matches:
            return json.dumps(
                {"ok": False, "error": "no_capability_match", "route": route},
                ensure_ascii=False,
            )
        cap_id = matches[0]["capability"]["id"]
        result = execute_runtime_capability(cap_id, message)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f"execute_capability error: {e}"


def _run_shell_tool(params: dict) -> str:
    try:
        from tools.shell_exec import run_shell

        command = params.get("command") or params.get("cmd") or params.get("script") or ""
        command = str(command).strip()
        if not command:
            return "run_shell error: missing command"
        return run_shell(
            command,
            cwd=str(params.get("cwd") or "project"),
            shell=params.get("shell"),
        )
    except Exception as e:
        return f"run_shell error: {e}"


def _capability_route_tool(params: dict) -> str:
    try:
        from intent_router import route_intent

        message = params.get("message") or params.get("text") or params.get("query") or params.get("user_text") or ""
        message = str(message).strip()
        if not message:
            return "route_capability_intent error: missing message"
        max_matches = int(params.get("max_matches", 4) or 4)
        return json.dumps(route_intent(message, max_matches=max_matches), ensure_ascii=False)
    except Exception as e:
        return f"route_capability_intent error: {e}"


def _task_orchestration_tool(params: dict) -> str:
    try:
        message = params.get("message", "").strip()
        if not message:
            return "run_task_orchestration error: missing message"
        base = orchestration_defaults()
        result = run_orchestration(
            message,
            {
                "planner_model": params.get("planner_model") or base["planner_model"],
                "coder_model": params.get("coder_model") or base["coder_model"],
                "reviewer_model": params.get("reviewer_model") or base["reviewer_model"],
                "vision_model": params.get("vision_model") or base["vision_model"],
                "speech_model": params.get("speech_model") or base["speech_model"],
                "evolution_context": _evolution_profile_tool({}),
            },
        )
        return result["final_output"]
    except Exception as e:
        return f"run_task_orchestration error: {e}"


def _notebook_ingest_tool(params: dict) -> str:
    title = (params.get("title") or "笔记").strip() or "笔记"
    body = (params.get("text") or params.get("body") or "").strip()
    if not body:
        return "notebook_ingest error: missing text"
    try:
        return json.dumps(ingest_notebook_corpus(title, body), ensure_ascii=False)
    except Exception as e:
        return f"notebook_ingest error: {e}"


def _notebook_synthesize_tool(params: dict) -> str:
    rt = get_runtime()
    title = (params.get("title") or "合成").strip() or "合成"
    body = (params.get("text") or "").strip()
    if not body:
        return "notebook_synthesize error: missing text"
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是资料整理助手。把用户给的长材料整理成结构化中文笔记："
                    "小标题、要点列表、待核实问题；不要空话套话。"
                ),
            },
            {"role": "user", "content": f"标题偏好：{title}\n\n材料：\n{body}"},
        ]
        out = chat_complete_sync(messages, rt.default_chat_model, temperature=0.2)
        ing = ingest_notebook_corpus(f"{title} · 合成", out)
        return json.dumps({"synthesis": out, "ingest": ing}, ensure_ascii=False)
    except Exception as e:
        return f"notebook_synthesize error: {e}"


def _generate_image_tool(params: dict) -> str:
    try:
        from local_agent_api import GenImageBody, generate_image

        prompt = (params.get("prompt") or "").strip() or "abstract"
        output_path = (params.get("output_path") or "outputs/agent_sd.png").strip()
        return json.dumps(
            generate_image(GenImageBody(prompt=prompt, output_path=output_path)),
            ensure_ascii=False,
        )
    except Exception as e:
        return f"generate_image error: {e}"


def _generate_video_tool(params: dict) -> str:
    try:
        from local_agent_api import GenVideoBody, generate_video

        raw = params.get("image_paths")
        if isinstance(raw, str):
            paths = [p.strip() for p in raw.replace("，", ",").split(",") if p.strip()]
        elif isinstance(raw, list):
            paths = [str(p).strip() for p in raw if str(p).strip()]
        else:
            paths = []
        prompt = (params.get("prompt") or "").strip()
        output_path = (params.get("output_path") or "outputs/agent_video.mp4").strip()
        fps = float(params.get("fps", 1.0) or 1.0)
        if not paths and not prompt:
            return "generate_video error: need prompt (AI video) or image_paths (slideshow)"
        return json.dumps(
            generate_video(
                GenVideoBody(
                    prompt=prompt,
                    image_paths=paths,
                    output_path=output_path,
                    fps=fps,
                )
            ),
            ensure_ascii=False,
        )
    except Exception as e:
        return f"generate_video error: {e}"


def _text_to_speech_tool(params: dict) -> str:
    try:
        from local_agent_api import TTSBody, text_to_speech

        text = (params.get("text") or "").strip()
        if not text:
            return "text_to_speech error: missing text"
        output_path = (params.get("output_path") or "outputs/agent_tts.wav").strip()
        return json.dumps(
            text_to_speech(TTSBody(text=text, output_path=output_path)),
            ensure_ascii=False,
        )
    except Exception as e:
        return f"text_to_speech error: {e}"


def _run_project_check_tool(params: dict) -> str:
    from pathlib import Path

    target = str(params.get("target") or "all").strip().lower()
    root = Path(__file__).resolve().parent.parent
    backend = root / "backend"
    frontend = root / "frontend"
    results: list[str] = []

    def run(label: str, cmd: list[str], cwd: Path) -> None:
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=180,
            )
            output = (completed.stdout or "") + (("\nSTDERR:\n" + completed.stderr) if completed.stderr else "")
            results.append(
                f"## {label}\nexit_code={completed.returncode}\n{output[-4000:] if output else '(no output)'}"
            )
        except Exception as e:
            results.append(f"## {label}\nerror={e}")

    if target in ("backend", "all", "api"):
        run(
            "backend py_compile",
            [
                sys.executable,
                "-m",
                "py_compile",
                "main.py",
                "agent.py",
                "observe.py",
                "tools/search.py",
            ],
            backend,
        )
    if target in ("frontend", "all", "ui"):
        npm_cmd = "npm.cmd" if sys.platform.startswith("win") else "npm"
        run("frontend build", [npm_cmd, "run", "build"], frontend)
    return "\n\n".join(results)


def _web_search_tool(params: dict) -> str:
    q = (
        params.get("query")
        or params.get("q")
        or params.get("search")
        or params.get("keywords")
        or params.get("text")
        or ""
    )
    if isinstance(q, (list, tuple)):
        q = " ".join(str(x) for x in q)
    q = str(q).strip()
    if not q:
        return (
            'web_search error: 缺少搜索关键词。请在 parameters 里提供 query（字符串），例如 {"query": "最新 AI 新闻"}。'
        )
    return web_search(q)


def _parallel_subagents_tool(params: dict) -> str:
    raw = params.get("tasks") or params.get("prompts") or []
    if isinstance(raw, str):
        raw = [line.strip() for line in raw.splitlines() if line.strip()]
    if not isinstance(raw, list):
        return "run_parallel_subagents error: tasks 须为数组或非空多行文本"
    model = (params.get("model") or "").strip() or None
    return run_parallel_subagents_sync([str(x) for x in raw], model=model)


def _browser_fill_form_tool(params: dict) -> str:
    from tools.browser import browser_fill_form

    fields = params.get("fields") or params.get("form") or {}
    if isinstance(fields, str):
        try:
            fields = json.loads(fields)
        except json.JSONDecodeError:
            fields = {}
    if not isinstance(fields, dict):
        fields = {}
    return browser_fill_form(
        params.get("url") or "",
        fields,
        params.get("submit_selector"),
    )


def _lazy_execute_python(params: dict) -> str:
    from tools.code_exec import execute_python

    return execute_python(params["code"])


def _lazy_open_url(params: dict) -> str:
    from tools.external_control import open_url

    return open_url(params.get("url") or params.get("href") or params.get("link") or "")


def _lazy_open_path(params: dict) -> str:
    from tools.external_control import open_path

    return open_path(params.get("path") or params.get("target") or "")


def _lazy_get_foreground_window(_: dict) -> str:
    from tools.external_control import get_foreground_window

    return get_foreground_window()


def _lazy_list_windows(params: dict) -> str:
    from tools.external_control import list_windows

    return list_windows(int(params.get("limit", 30) or 30))


def _lazy_focus_window(params: dict) -> str:
    from tools.external_control import focus_window

    return focus_window(params.get("title") or params.get("window") or params.get("name") or "")


def _lazy_send_hotkey(params: dict) -> str:
    from tools.external_control import send_hotkey

    return send_hotkey(params.get("keys") or params.get("hotkey") or "")


def _lazy_type_text(params: dict) -> str:
    from tools.external_control import type_text

    return type_text(params.get("text") or params.get("content") or "")


def _lazy_click_screen(params: dict) -> str:
    from tools.external_control import click_screen

    return click_screen(params.get("x"), params.get("y"))


def _lazy_browser_navigate(params: dict) -> str:
    from tools.browser import browser_navigate

    return browser_navigate(
        params.get("url") or params.get("href") or "",
        int(params.get("wait_ms", 2000) or 2000),
        bool(params.get("screenshot", False)),
    )


def _lazy_browser_screenshot(params: dict) -> str:
    from tools.browser import browser_screenshot

    return browser_screenshot(
        params.get("url") or params.get("href") or "",
        (params.get("output_path") or "outputs/browser_shot.png"),
    )


def _lazy_browser_click_and_extract(params: dict) -> str:
    from tools.browser import browser_click_and_extract

    return browser_click_and_extract(
        params.get("url") or "",
        params.get("selector") or "",
        params.get("extract_selector") or "body",
    )


def _lazy_browser_playwright(params: dict) -> str:
    from tools.browser import browser_playwright

    return browser_playwright(
        params.get("url") or params.get("href") or "",
        params.get("action") or params.get("mode") or "navigate",
        params.get("selector") or "",
        params.get("text") or params.get("value") or "",
        params.get("extract_selector") or "body",
        params.get("output_path") or "outputs/browser_shot.png",
        int(params.get("wait_ms", 2000) or 2000),
    )


TOOL_MAP = {
    "route_capability_intent": lambda p: _capability_route_tool(p),
    "execute_capability": lambda p: _execute_capability_tool(p),
    "run_shell": lambda p: _run_shell_tool(p),
    "web_search": lambda p: _web_search_tool(p),
    "local_search": lambda p: local_search(
        p.get("query") or p.get("q") or p.get("search") or "",
        int(p.get("limit", 6) or 6),
        bool(p.get("scrape", False)),
    ),
    "local_scrape_url": lambda p: local_scrape_url(
        p.get("url") or p.get("href") or p.get("link") or "",
        int(p.get("max_chars", 12000) or 12000),
    ),
    "read_file": lambda p: read_file(p["path"]),
    "write_file": lambda p: write_file(p["path"], p["content"]),
    "list_files": lambda p: list_files(p.get("directory") or p.get("path") or "~/Desktop"),
    "execute_python": lambda p: _lazy_execute_python(p),
    "get_system_info": lambda p: get_system_info(p),
    "get_gpu_status": lambda p: get_gpu_status(p),
    "optimize_gpu_memory": lambda p: optimize_gpu_memory(p),
    "get_process_list": lambda p: get_process_list(p),
    "kill_process": lambda p: kill_process(p),
    "get_network_status": lambda p: get_network_status(p),
    "search_files": lambda p: search_files(p),
    "get_device_profile": lambda p: _device_profile_tool(p),
    "get_recent_desktop_files": lambda p: _recent_desktop_files_tool(p),
    "get_recent_work_summary": lambda p: _recent_work_summary_tool(p),
    "get_evolution_profile": lambda p: _evolution_profile_tool(p),
    "run_task_orchestration": lambda p: _task_orchestration_tool(p),
    "notebook_ingest": lambda p: _notebook_ingest_tool(p),
    "notebook_synthesize": lambda p: _notebook_synthesize_tool(p),
    "generate_image": lambda p: _generate_image_tool(p),
    "generate_video": lambda p: _generate_video_tool(p),
    "generate_ai_video": lambda p: _generate_video_tool(p),
    "text_to_speech": lambda p: _text_to_speech_tool(p),
    "run_project_check": lambda p: _run_project_check_tool(p),
    "open_url": lambda p: _lazy_open_url(p),
    "open_path": lambda p: _lazy_open_path(p),
    "get_foreground_window": lambda p: _lazy_get_foreground_window(p),
    "list_windows": lambda p: _lazy_list_windows(p),
    "focus_window": lambda p: _lazy_focus_window(p),
    "send_hotkey": lambda p: _lazy_send_hotkey(p),
    "type_text": lambda p: _lazy_type_text(p),
    "click_screen": lambda p: _lazy_click_screen(p),
    "browser_navigate": lambda p: _lazy_browser_navigate(p),
    "browser_playwright": lambda p: _lazy_browser_playwright(p),
    "browser_screenshot": lambda p: _lazy_browser_screenshot(p),
    "browser_click_and_extract": lambda p: _lazy_browser_click_and_extract(p),
    "browser_fill_form": lambda p: _browser_fill_form_tool(p),
    "run_parallel_subagents": lambda p: _parallel_subagents_tool(p),
    "http_request": lambda p: http_request(
        p.get("url") or p.get("href") or "",
        p.get("method") or "GET",
        p.get("headers"),
        p.get("body") or p.get("json") or p.get("data"),
        float(p.get("timeout_sec", 30) or 30),
    ),
    "query_database": lambda p: query_database(
        p.get("path") or p.get("db_path") or p.get("database") or p.get("db") or "",
        p.get("sql") or p.get("query") or "",
        int(p.get("limit", 50) or 50),
    ),
    "mcp_invoke": lambda p: mcp_invoke(
        p.get("server") or "builtin",
        p.get("tool") or p.get("name") or "",
        p.get("arguments") if isinstance(p.get("arguments"), dict) else p,
    ),
}


def _normalize_parsed_tool(data: dict) -> dict:
    """把模型常犯的扁平字段 / OpenAI 风格 arguments 合并进 parameters，避免 KeyError。"""
    name = data.get("name")
    if name not in TOOL_MAP:
        return data
    params = data.get("parameters")
    if not isinstance(params, dict):
        params = {}
    args = data.get("arguments")
    if isinstance(args, dict):
        for k, v in args.items():
            params.setdefault(k, v)
    reserved = {"name", "parameters", "arguments", "id", "type"}
    for k, v in data.items():
        if k in reserved or k in params:
            continue
        params[k] = v
    out = dict(data)
    out["parameters"] = params
    return out
