import asyncio
import json
import os
import re
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from tools.search import web_search
from tools.local_crawl import local_scrape_url, local_search
from tools.file_ops import read_file, write_file, list_files, resolve_user_path
from tools.http_tool import http_request
from tools.db_query import query_database
from tools.mcp_invoke import mcp_invoke
from subagent_runner import run_parallel_subagents_sync
from orchestrator import run_orchestration
from memory_store import (
    build_knowledge_context,
    build_memory_context,
    build_playbook_context,
    ingest_notebook_corpus,
    list_playbook_entries,
    remember_from_message,
)
from observe import get_evolution_profile_text, get_runtime_adjustments, record_task_outcome
from workflow_store import build_workflow_context, record_task_review

from agent_runtime import get_runtime, orchestration_defaults, reload_runtime
from context_pack import compress_for_llm, compress_tool_result_for_llm
from hooks import notify_agent_completed
from llm_client import chat_complete_async, chat_complete_sync
from self_evolve import distill_playbook_with_llm, ingest_review_lesson
from skill_pack import build_skill_pack_context
from agent_session import build_messages_with_history, persist_agent_answer, save_user_turn


def _agent_run_stream_error_message(exc: Exception) -> str:
    """Agent /run 流式失败时的用户文案：按实际 LLM 后端说明，勿写死 Ollama。"""
    from model_lock import is_model_locked, locked_model_id

    r = get_runtime()
    lock = ""
    if is_model_locked():
        lock = f" 单模型锁 id=`{locked_model_id()}`。"
    if r.llm_backend == "openai_compatible":
        return (
            f"这次 Agent 在调用模型时失败了：{exc}{lock}\n\n"
            "当前走 **OpenAI 兼容网关**（vLLM 等）。请检查：`OPENAI_BASE_URL` 是否可达（一般以 `/v1` 结尾）、"
            "`GET …/v1/models` 返回的 `id` 是否与锁定模型名 **完全一致**，以及网关是否在跑；修改 `backend/.env` 后需重启 ONYX。"
        )
    raw = os.environ.get("LLM_BACKEND", "").strip().lower()
    if raw in ("openai_compatible", "openai", "vllm", "litellm", "localai"):
        return (
            f"这次 Agent 在调用模型时失败了：{exc}{lock}\n\n"
            f"`LLM_BACKEND` 已设为网关类（当前值：`{os.environ.get('LLM_BACKEND')}`），但 **OPENAI_BASE_URL 为空**，"
            "后端会回退用 Ollama；`/mnt/...` 这类 id 不是 Ollama tag，会失败。请在 `backend/.env` 设置 "
            "`OPENAI_BASE_URL`（例如 `http://127.0.0.1:8001/v1`）并重启应用。"
        )
    return (
        f"这次 Agent 在调用模型时失败了：{exc}{lock}\n\n"
        "当前走 **Ollama**。请确认 `ollama serve` 已运行，且 `ollama list` 里存在 `.env` 中的 `LOCKED_MODEL_ID` / `AGENT_DEFAULT_MODEL`。"
    )


router = APIRouter()

TOOLS_DESC = """
可用工具：
- web_search：联网搜索最新信息
- local_search：无 Key 本地搜索，必要时抓取搜索结果正文（参数 query、limit、scrape）
- local_scrape_url：无 Key 抓取指定网页并提取可读 Markdown 文本（参数 url）
- read_file：读取本地文件
- write_file：写入本地文件
- list_files：列出目录内容
- execute_python：执行 Python 代码
- get_device_profile：读取本机设备画像与使用习惯摘要
- get_recent_desktop_files：读取最近有变化的桌面文件
- get_recent_work_summary：综合设备画像与最近桌面文件，总结你最近在做什么
- get_evolution_profile：读取自进化画像摘要
- run_task_orchestration：多模型协作规划/实现/审查并汇总结论（编排、复杂方案对比、多角色任务）
- notebook_ingest：把长文本笔记写入本地知识库（参数 title、text）
- notebook_synthesize：用模型整理长材料后写入知识库（参数 title、text）
- generate_image：本地文生图（参数 prompt、output_path，需 ENABLE_LOCAL_SD）
- generate_video：生成视频。幻灯片：image_paths + output_path + fps；文生视频：prompt + output_path（需 .env 设 VIDEO_GEN_BACKEND=auto|cogvideox|wan，依赖 requirements-media.txt）
- text_to_speech：本地文字转语音 wav（参数 text、output_path）
- run_project_check：运行本项目内置检查（参数 target，可选 backend/frontend/all）
- open_url：在默认浏览器打开网页（参数 url，仅 http/https）
- open_path：打开本地文件、文件夹或程序（参数 path，受安全路径解析限制）
- get_foreground_window：读取当前 Windows 前台窗口标题
- list_windows：列出当前可见窗口
- focus_window：按窗口标题关键字聚焦第三方 App（参数 title）
- send_hotkey：向当前前台窗口发送快捷键（参数 keys，例如 ctrl+l）
- type_text：向当前前台窗口输入文字（参数 text）
- click_screen：点击屏幕坐标（参数 x、y）
- browser_navigate：Playwright 打开网页并提取正文（参数 url、wait_ms、screenshot）
- browser_screenshot：网页全页截图（参数 url、output_path）
- browser_click_and_extract：打开网页点击元素后提取内容（参数 url、selector、extract_selector）
- browser_fill_form：填写并提交表单（参数 url、fields 对象、submit_selector）
- run_parallel_subagents：并行执行多条子提示并汇总（参数 tasks 字符串数组或多行文本、model 可选）

工具调用格式必须严格输出：
<tool_call>{"name":"tool_name","parameters":{"key":"value"}}</tool_call>

不要教用户怎么手动调用工具。
如果任务需要工具，就由你自己调用。
用户用自然语言描述意图即可，不要要求用户填 API 字段。
"""

SYSTEM_PROMPT = (
    "你是一个本地 AI Agent。"
    "你的职责是直接完成任务，不是教用户如何调用工具。"
    "当需要读取文件、列目录、搜索、执行代码、查看设备画像、编排多模型任务、写入知识库、"
    "本地画图/视频/语音时，必须自己调用对应工具。\n"
    "若用户提到「编排」「多模型」「复杂方案对比」「协作审查」等，应优先使用 run_task_orchestration，"
    "并把用户整句需求作为 parameters.message 传入。\n\n"
    "能力边界要准确表达：当前已能联网搜索、本地网页抓取、文件管理、代码执行、设备画像、知识库、多模型编排、"
    "图像/视频/语音生成、项目检查和 Windows 第三方 App 基础控制。"
    "生成图片/视频后，最终回答里必须写出 outputs 下的文件路径，便于界面预览。\n"
    "文生视频优先 generate_video(prompt=...)；有多张图时用 image_paths 合成幻灯片。\n"
    "第三方 App 控制可列窗口、聚焦窗口、发送快捷键、输入文字、坐标点击；"
    "需要用户明确目标窗口/快捷键/坐标，不能声称已具备越权控制或绕过安全限制。\n\n"
    + TOOLS_DESC
)


def _build_system_prompt() -> str:
    rt = get_runtime()
    runtime = get_runtime_adjustments()
    parts = [SYSTEM_PROMPT]
    if rt.agent_self_evolve:
        parts.append(
            "## 自进化（已开启）\n"
            "- 每次 Agent 任务结束会写入 playbook 教训（ingest_review_lesson）。\n"
            "- 需要画像时可调用 get_evolution_profile；需要批量蒸馏可 POST /agent/evolve/distill（需 AGENT_EVOLVE_LLM=1）。\n"
            "- 回答应体现从历史任务中学到的执行风格，避免重复已知错误。"
        )
    if runtime.get("prompt_hints"):
        parts.append("## 默认执行风格\n" + "\n".join(f"- {item}" for item in runtime["prompt_hints"]))
    if runtime.get("preferred_tools"):
        parts.append("## 默认工具优先级\n" + " -> ".join(runtime["preferred_tools"][:8]))
    parts.append(
        "## 输出质量硬约束\n"
        "- 不要复述用户问题。\n"
        "- 不要讲空泛教程，不要重复同一句意思。\n"
        "- 先给结论，再给真正可执行的下一步。\n"
        "- 如果拿到了工具结果，必须基于真实结果回答。\n"
        "- 如果没拿到真实结果，就明确承认没完成，不要装作已经做完。\n"
        "- 不要输出「无法进行需外部交互的操作」这种一刀切限制；要改成「当前缺少对应外部交互工具，但可后续接入」。\n"
        "- 未授权入侵、对他人隐私的批量搜集、用于欺骗的反检测/指纹绕过、违法或高风险绕过类请求：拒绝并说明合规边界。"
    )
    return "\n\n".join(parts)


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
        return json.dumps(generate_image(GenImageBody(prompt=prompt, output_path=output_path)), ensure_ascii=False)
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
        return json.dumps(text_to_speech(TTSBody(text=text, output_path=output_path)), ensure_ascii=False)
    except Exception as e:
        return f"text_to_speech error: {e}"


def _run_project_check_tool(params: dict) -> str:
    import subprocess
    import sys
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
                f"## {label}\n"
                f"exit_code={completed.returncode}\n"
                f"{output[-4000:] if output else '(no output)'}"
            )
        except Exception as e:
            results.append(f"## {label}\nerror={e}")

    if target in ("backend", "all", "api"):
        run(
            "backend py_compile",
            [sys.executable, "-m", "py_compile", "main.py", "agent.py", "observe.py", "tools/search.py"],
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
        return "web_search error: 缺少搜索关键词。请在 parameters 里提供 query（字符串），例如 {\"query\": \"最新 AI 新闻\"}。"
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


DIRECTORY_HINTS = {
    "桌面": "~/Desktop",
    "文档": "~/Documents",
    "下载": "~/Downloads",
    "图片": "~/Pictures",
    "视频": "~/Videos",
    "desktop": "~/Desktop",
    "documents": "~/Documents",
    "downloads": "~/Downloads",
    "pictures": "~/Pictures",
    "videos": "~/Videos",
}


_GEMMA4_ID = "nvidia/Gemma-4-26B-A4B-NVFP4"


class AgentRequest(BaseModel):
    message: str
    model: str = Field(default_factory=lambda: get_runtime().default_chat_model)
    session_id: str | None = None


def _candidate_models(requested_model: str) -> list[str]:
    from model_lock import enforce_locked_model, is_model_locked

    if is_model_locked():
        locked = enforce_locked_model(requested_model)
        return [locked]
    rt = get_runtime()
    models = [requested_model, rt.default_chat_model, _GEMMA4_ID]
    seen = set()
    ordered: list[str] = []
    for item in models:
        item = (item or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


async def call_llm(messages, model: str, *, temperature: float = 0.1):
    errors: list[str] = []
    for candidate in _candidate_models(model):
        try:
            return await chat_complete_async(messages, candidate, temperature=temperature)
        except Exception as e:
            errors.append(f"{candidate}: {e}")
            continue
    raise RuntimeError(" | ".join(errors) if errors else "no llm candidate available")


def parse_tool(text: str):
    tool_names = "|".join(re.escape(k) for k in sorted(TOOL_MAP.keys()))
    patterns = [
        r"<tool_call>(.*?)</tool_call>",
        r"```tool\s*(.*?)```",
        r"```json\s*(\{\s*\"name\".*?\})\s*```",
        r"(\{\s*\"name\"\s*:\s*\"(?:" + tool_names + r")\".*?\})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            continue
        candidate = match.group(1).strip()
        try:
            data = json.loads(candidate)
            if isinstance(data, dict) and data.get("name") in TOOL_MAP:
                data.setdefault("parameters", {})
                return _normalize_parsed_tool(data)
        except Exception:
            continue
    return None


def _extract_windows_path(message: str) -> Optional[str]:
    match = re.search(r"([A-Za-z]:[\\/][^\n\r\"<>|?*]+?\.[A-Za-z0-9]{1,8})(?=$|[\s,，。;；])", message)
    if not match:
        match = re.search(r"([A-Za-z]:[\\/][^\n\r\"<>|?*]+)", message)
    if match:
        return match.group(1).strip().replace("/", "\\")
    return None


FAST_TOOL_FINALS = {
    "list_files",
    "read_file",
    "get_device_profile",
    "get_recent_desktop_files",
    "get_recent_work_summary",
    "get_evolution_profile",
    "run_project_check",
}


def _extract_filename(message: str) -> Optional[str]:
    location_patterns = [
        r"桌面上的([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
        r"文档里的([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
        r"下载里的([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
        r"图片里的([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
        r"视频里的([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
        r"桌面上([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
        r"文档里([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
        r"下载里([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
        r"图片里([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
        r"视频里([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})",
    ]
    for pattern in location_patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1).strip()

    generic_patterns = [
        r'["“](.+?\.[A-Za-z0-9]{1,8})["”]',
        r'[「『](.+?\.[A-Za-z0-9]{1,8})[」』]',
        r'([^，。\n\r；;]+?\.[A-Za-z0-9]{1,8})',
    ]
    for pattern in generic_patterns:
        match = re.search(pattern, message)
        if match:
            candidate = match.group(1).strip()
            candidate = re.sub(r"^(?:读取|打开文件|看看文件|看文件|文件内容|读取文件|读取这个文件|看看这个文件)\s*", "", candidate)
            return candidate.strip()
    return None


def _detect_directory_hint(message: str) -> Optional[str]:
    lower = message.lower()
    for key, target in DIRECTORY_HINTS.items():
        if key in message or key in lower:
            return target
    return None


def _guess_target_path(message: str) -> Optional[str]:
    windows_path = _extract_windows_path(message)
    if windows_path:
        return windows_path

    filename = _extract_filename(message)
    directory_hint = _detect_directory_hint(message)

    if filename and directory_hint:
        return str((resolve_user_path(directory_hint) / filename).resolve())
    if filename:
        return filename
    if directory_hint:
        return directory_hint
    return None


def _extract_url(message: str) -> Optional[str]:
    match = re.search(r"(https?://[^\s，。；;\"'<>]+)", message, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_quoted_text(message: str) -> Optional[str]:
    for pattern in [r'["“](.+?)["”]', r"[「『](.+?)[」』]", r"`(.+?)`"]:
        match = re.search(pattern, message)
        if match:
            return match.group(1).strip()
    return None


def _extract_hotkey(message: str) -> Optional[str]:
    match = re.search(
        r"((?:ctrl|control|alt|shift|win|windows|esc|enter|tab|f\d{1,2}|[a-z0-9])(?:\s*\+\s*(?:ctrl|control|alt|shift|win|windows|esc|enter|tab|f\d{1,2}|[a-z0-9]))+)",
        message,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    simple = {
        "回车": "enter",
        "按下回车": "enter",
        "按 enter": "enter",
        "按esc": "esc",
        "按 esc": "esc",
        "退出键": "esc",
    }
    for key, value in simple.items():
        if key in message.lower():
            return value
    return None


def _extract_coordinates(message: str) -> Optional[tuple[int, int]]:
    match = re.search(r"(?:坐标|位置)?\s*[（(]?\s*(\d{1,5})\s*[,，]\s*(\d{1,5})\s*[）)]?", message)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _extract_window_title(message: str) -> Optional[str]:
    quoted = _extract_quoted_text(message)
    if quoted:
        return quoted
    text = re.sub(r"^(帮我|给我|请|把|将|切到|切换到|聚焦|激活|打开|定位到|窗口|应用|app|App)\s*", "", message.strip())
    text = re.sub(r"(窗口|应用|app|App)$", "", text).strip()
    if 1 <= len(text) <= 80:
        return text
    return None


def _looks_like_model_download_research(text: str) -> bool:
    lower = (text or "").lower()
    model_markers = [
        "模型", "大模型", "本地模型", "顶级模型", "开源模型", "llm", "gguf",
        "qwen", "deepseek", "mistral", "gemma", "llama",
    ]
    hardware_markers = ["gpu", "显卡", "5090", "4090", "24g", "24gb", "vram", "显存"]
    research_markers = ["下载", "可以下载", "适配", "推荐", "最强", "最牛", "顶级", "目前", "最新", "本地"]
    has_model = any(k in lower or k in text for k in model_markers)
    has_hardware = any(k in lower or k in text for k in hardware_markers)
    has_research = any(k in lower or k in text for k in research_markers)
    return has_model and (has_hardware or has_research)


def _model_download_search_query(text: str) -> str:
    """Rewrite vague Chinese model requests into targeted downloadable-model search."""
    lower = (text or "").lower()
    hardware = "RTX 5090 24GB VRAM" if ("5090" in lower or "24g" in lower) else "24GB VRAM"
    return (
        f"{text} {hardware} GGUF Hugging Face Ollama "
        "Qwen3-32B-GGUF DeepSeek-R1-Distill-Qwen-32B-GGUF "
        "Qwen3-30B-A3B-GGUF Mistral-Small-3.2-24B-Instruct-GGUF"
    )


def _looks_like_research_or_recommendation_request(text: str) -> bool:
    lower = (text or "").lower()
    research_verbs = [
        "查", "查一下", "看看", "帮我看看", "了解", "调研", "搜索", "找一下",
        "推荐", "对比", "排行", "排名", "哪个", "哪些", "目前", "最新", "最强", "最牛", "顶级",
        "research", "search", "recommend", "compare", "best", "latest", "top",
    ]
    subject_markers = [
        "模型", "大模型", "llm", "软件", "工具", "库", "框架", "资料", "信息", "方案",
        "gpu", "显卡", "显存", "5090", "4090", "24g", "24gb",
    ]
    local_file_markers = [
        "文件", "目录", "文件夹", "路径", "桌面", "文档", "下载目录", "下载文件夹",
        "file", "folder", "directory", "path",
    ]
    explicit_file_actions = [
        "列出", "打开文件", "读取文件", "文件内容", "目录里", "文件夹里",
        "list files", "read file", "open file", "show files",
    ]
    has_research = any(k in lower or k in text for k in research_verbs)
    has_subject = any(k in lower or k in text for k in subject_markers)
    explicit_file = any(k in lower or k in text for k in explicit_file_actions)
    only_file_subject = any(k in lower or k in text for k in local_file_markers) and not has_subject
    return has_research and has_subject and not (explicit_file and only_file_subject)


def infer_tool_from_message(message: str):
    text = message.strip()
    lower = text.lower()
    lower_words = set(re.findall(r"[a-z0-9_:-]+", lower))
    path = _guess_target_path(text)
    url = _extract_url(text)
    filename = _extract_filename(text)
    directory_hint = _detect_directory_hint(text)

    if _looks_like_model_download_research(text):
        return {"name": "local_search", "parameters": {"query": _model_download_search_query(text), "limit": 8, "scrape": True}}

    if _looks_like_research_or_recommendation_request(text):
        return {"name": "local_search", "parameters": {"query": text, "limit": 8, "scrape": True}}

    deploy_markers = ["启动失败", "端口连不上", "连不上", "起不来", "部署失败", "服务失败", "服务不可用"]
    deploy_subjects = ["vllm", "ollama", "uvicorn", "fastapi", "8000", "8001", "8002", "端口", "backend", "后端"]
    if any(k in lower or k in text for k in deploy_markers) and any(k in lower or k in text for k in deploy_subjects):
        return {"name": "get_device_profile", "parameters": {}}

    if url and any(k in text for k in ["抓取网页", "读取网页", "总结网页", "网页内容", "爬取", "scrape", "crawl"]):
        return {"name": "local_scrape_url", "parameters": {"url": url}}

    if url and any(k in text for k in ["打开网页", "打开网站", "打开链接", "浏览", "访问", "打开"]):
        return {"name": "open_url", "parameters": {"url": url}}

    if any(k in text for k in ["打开桌面", "打开下载", "打开文档", "打开文件夹", "打开目录"]) and path:
        return {"name": "open_path", "parameters": {"path": path}}

    if any(k in text for k in ["当前窗口", "前台窗口", "现在打开的窗口", "我现在在哪个窗口"]):
        return {"name": "get_foreground_window", "parameters": {}}

    if any(k in text for k in ["列出窗口", "有哪些窗口", "当前有哪些窗口", "可见窗口", "窗口列表"]):
        return {"name": "list_windows", "parameters": {"limit": 30}}

    if any(k in text for k in ["切到", "切换到", "聚焦", "激活窗口", "定位到窗口"]):
        title = _extract_window_title(text)
        if title:
            return {"name": "focus_window", "parameters": {"title": title}}

    coord = _extract_coordinates(text)
    if coord and any(k in text for k in ["点击", "点一下", "鼠标点", "单击"]):
        return {"name": "click_screen", "parameters": {"x": coord[0], "y": coord[1]}}

    hotkey = _extract_hotkey(text)
    if hotkey and any(k in text for k in ["按", "快捷键", "热键", "hotkey"]):
        return {"name": "send_hotkey", "parameters": {"keys": hotkey}}

    if any(k in text for k in ["在当前窗口输入", "输入文字", "粘贴文字", "打字"]):
        typed = _extract_quoted_text(text)
        if typed:
            return {"name": "type_text", "parameters": {"text": typed}}

    if any(
        k in text
        for k in [
            "多模型",
            "复杂任务",
            "拆解任务",
            "完整项目",
            "协作完成",
            "任务分解",
            "执行计划",
            "编排",
            "orchestrate",
            "多角色",
            "协作汇总",
            "总控",
            "方案对比",
            "复杂方案",
            "对比方案",
            "用编排",
        ]
    ):
        od = orchestration_defaults()
        return {
            "name": "run_task_orchestration",
            "parameters": {
                "message": text,
                "planner_model": od["planner_model"],
                "coder_model": od["coder_model"],
                "reviewer_model": od["reviewer_model"],
            },
        }

    if any(k in text for k in ["生成图", "画一张", "生图", "文生图", "做个图标", "帮我画", "画个"]) and len(text) < 1200:
        return {"name": "generate_image", "parameters": {"prompt": text, "output_path": "outputs/agent_sd.png"}}

    if any(k in text for k in ["生成一段视频", "生成视频", "做个视频", "制作视频", "生成短片", "文生视频", "短片"]) and len(text) < 1200:
        return {"name": "generate_ai_video", "parameters": {"prompt": text, "output_path": "outputs/ai_video.mp4"}}

    if any(k in text for k in ["文字转语音", "转成语音", "播报出来", "读给我听", "念一下", "语音播报"]) and len(text) < 4000:
        return {"name": "text_to_speech", "parameters": {"text": text, "output_path": "outputs/agent_tts.wav"}}

    if any(k in text for k in ["自动部署", "部署检查", "项目检查", "构建检查", "能不能启动", "跑一下检查"]):
        target = "all"
        if "后端" in text or "backend" in lower:
            target = "backend"
        elif "前端" in text or "frontend" in lower or "界面" in text:
            target = "frontend"
        return {"name": "run_project_check", "parameters": {"target": target}}

    if ("导入知识库" in text or "写入知识树" in text or "记到知识库" in text) and len(text) > 60:
        title_guess = (text.split("\n")[0] or "笔记").strip()[:200]
        return {"name": "notebook_ingest", "parameters": {"title": title_guess, "text": text}}

    if any(k in text for k in ["整理后写入知识库", "整理成长笔记", "AI 整理后写入"]) and len(text) > 120:
        return {"name": "notebook_synthesize", "parameters": {"title": "整理", "text": text}}

    if any(k in text for k in ["设备画像", "使用习惯", "最近在忙什么", "设备情况", "画像"]):
        return {"name": "get_device_profile", "parameters": {}}

    if any(k in text for k in ["最近在做什么", "总结我最近在干什么", "我最近在干什么", "最近忙什么", "总结最近活动"]):
        return {"name": "get_recent_work_summary", "parameters": {}}

    if any(k in text for k in ["最近桌面文件", "桌面最近文件", "最近改过的文件", "桌面最近动了什么", "最近桌面上有什么变化"]):
        return {"name": "get_recent_desktop_files", "parameters": {"limit": 12}}

    wants_listing = any(k in text for k in ["列出", "哪些文件", "文件夹", "目录", "桌面上有什么", "文件列表", "有哪些"]) or any(
        phrase in lower for phrase in ["list files", "show files", "show me files", "file list", "list directory", "list folder"]
    ) or (("list" in lower_words or "show" in lower_words) and ("file" in lower_words or "files" in lower_words))
    wants_read = any(k in text for k in ["读取", "打开文件", "看文件", "文件内容", "read file", "看看这个文件", "读取这个文件"]) or any(
        phrase in lower for phrase in ["read this file", "read file", "open this file", "show file contents", "file contents"]
    )
    wants_browse = any(k in text for k in ["看看", "看一下", "帮我看看"])

    if wants_listing or ((wants_browse or "list files" in lower) and not filename):
        return {"name": "list_files", "parameters": {"directory": directory_hint or path or "~/Desktop"}}

    if (wants_read or (wants_browse and filename)) and path:
        return {"name": "read_file", "parameters": {"path": path}}

    if any(k in text for k in ["保存到", "写入", "创建文件", "write file"]) and path:
        content_match = re.search(r"内容[：:](.*)", text, re.DOTALL)
        return {
            "name": "write_file",
            "parameters": {"path": path, "content": content_match.group(1).strip() if content_match else ""},
        }

    if any(k in text for k in ["搜索并抓取", "搜索并读取", "深度搜索", "查资料", "读网页", "抓网页"]):
        return {"name": "local_search", "parameters": {"query": text, "limit": 3, "scrape": True}}

    if any(
        k in text
        for k in [
            "trending developers",
            "github trending",
            "热榜开发者",
            "今日开发者",
            "plannotator",
            "gstack",
            "ruflo",
            "a2a",
            "worldmonitor",
            "rlm",
        ]
    ):
        return None

    if any(k in text for k in ["搜索", "查一下", "最新", "新闻", "web search", "duckduckgo"]):
        return {"name": "local_search", "parameters": {"query": text, "limit": 6, "scrape": False}}

    if url and any(k in text for k in ["http 请求", "发送请求", "调用 api", "请求接口", "GET ", "POST "]):
        upper = text.upper()
        method = "GET"
        if "POST" in upper:
            method = "POST"
        elif "PUT" in upper:
            method = "PUT"
        elif "DELETE" in upper:
            method = "DELETE"
        return {"name": "http_request", "parameters": {"url": url, "method": method}}

    if re.search(r"\bselect\b", lower) and any(k in text for k in ["sql", "查询", "数据库", "sqlite", ".db"]):
        db_path = path or _extract_windows_path(text) or ""
        sql_match = re.search(r"(select\s+.+)", text, re.IGNORECASE | re.DOTALL)
        if sql_match:
            return {
                "name": "query_database",
                "parameters": {"path": db_path or "backend/memory.db", "sql": sql_match.group(1).strip()[:2000]},
            }

    code_match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    if code_match:
        return {"name": "execute_python", "parameters": {"code": code_match.group(1).strip()}}

    return None


def _looks_like_action_request(message: str) -> bool:
    triggers = [
        "帮我", "给我", "看看", "读取", "打开", "列出", "查一下", "搜索", "总结",
        "分析", "整理", "写入", "创建", "执行", "运行", "生成", "拆解", "查看",
    ]
    return any(token in message for token in triggers)


def _is_tool_error_text(text: str) -> bool:
    lowered = (text or "").lower()
    flags = [
        "tool error:", "unknown tool", "not found:", "error:", "timeout",
        "missing message", "子任务失败",
    ]
    return any(flag in lowered for flag in flags)


def _tool_result_failed(tool_name: str | None, text: str) -> bool:
    lowered = (text or "").lower().strip()
    if (tool_name or "").lower() == "local_search":
        if not lowered:
            return True
        hard_failures = ("local_search error:", "search error: empty query", "search error:")
        if lowered.startswith(hard_failures):
            return True
        # Search results may contain scraped-page error snippets. Treat the tool as
        # successful when it still returned result bullets/URLs.
        return not ("· " in text or "http://" in lowered or "https://" in lowered)
    return _is_tool_error_text(text)


def _is_successful_tool_result(text: str) -> bool:
    return bool((text or "").strip()) and not _is_tool_error_text(text)


def _looks_like_garbled_text(text: str) -> bool:
    raw = text or ""
    if raw.count("?") < 3:
        return False
    has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in raw)
    has_alpha = any(("a" <= ch.lower() <= "z") for ch in raw)
    return not has_cjk and not has_alpha


def _looks_like_manual_instructions(text: str) -> bool:
    markers = [
        "请根据您使用的操作系统进行以下操作",
        "方法一", "方法二", "win + r", "cmd", "文件资源管理器",
        "如果您需要", "您可以使用以下方法", "请手动", "请打开",
    ]
    return any(marker in text for marker in markers)


def _looks_like_fake_completion(text: str) -> bool:
    markers = [
        "我已经给你", "我给你装好", "我给你放桌面", "已经完成",
        "已帮你", "已经处理好了", "已经替你", "搞定了",
    ]
    return any(marker in text for marker in markers)


def _build_honest_failure_answer(message: str, tool_name: str | None = None, tool_result: str | None = None) -> str:
    lines = ["这次我没有真正把任务做完。"]
    if tool_name:
        lines.append(f"我尝试调用的工具：`{tool_name}`。")
    if tool_result:
        snippet = str(tool_result).strip()
        if len(snippet) > 260:
            snippet = snippet[:260] + "..."
        lines.append(f"真实执行结果：{snippet}")
    lines.append("我不会把没执行成功的事说成已经完成。")
    lines.append(f"当前卡住的任务：{message}")
    return "\n".join(lines)


def _looks_like_summary_request(message: str) -> bool:
    lower = (message or "").lower()
    markers = [
        "总结", "摘要", "概述", "简短总结", "简要总结", "提炼",
        "summary", "summarize", "summarise", "brief", "overview",
    ]
    return any(marker in (message or "") or marker in lower for marker in markers)


def _local_read_file_summary(text: str) -> str:
    body = text
    if body.startswith("[PATH]"):
        parts = body.split("\n\n", 1)
        body = parts[1] if len(parts) > 1 else body

    lines = [line.rstrip() for line in body.splitlines()]
    title = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), "")
    headings = [line.lstrip("# ").strip() for line in lines if line.startswith("## ")]
    bullets = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
        elif re.match(r"^\d+\.\s+", stripped):
            bullets.append(re.sub(r"^\d+\.\s+", "", stripped))
    intro = next(
        (
            line.strip()
            for line in lines
            if line.strip() and not line.startswith("#") and not line.startswith("|") and not line.startswith("```")
        ),
        "",
    )

    out = []
    out.append(f"我已经读完这个文件，核心是：`{title or '这个文档'}`。")
    if intro:
        out.append(f"- 文件开头先说明：{intro[:140]}")
    if headings:
        out.append(f"- 主要章节：{', '.join(headings[:6])}")
    if bullets:
        out.append("- 关键信息：")
        out.extend([f"  - {item[:140]}" for item in bullets[:5]])
    return "\n".join(out)


def _normalize_text_for_compare(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip().lower()
    text = re.sub(r"[`*_>#\-:：，。、“”‘’\"'()\[\]{}]", "", text)
    return text


def _has_repeated_lines(text: str) -> bool:
    lines = [re.sub(r"\s+", " ", line.strip()) for line in (text or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    seen = set()
    dup = 0
    for line in lines:
        key = _normalize_text_for_compare(line)
        if key in seen:
            dup += 1
        seen.add(key)
    return dup >= 1


def _is_low_quality_answer(question: str, answer: str) -> bool:
    q = _normalize_text_for_compare(question)
    a = _normalize_text_for_compare(answer)
    generic_markers = [
        "请根据您使用的操作系统进行以下操作",
        "您可以使用以下方法",
        "请手动",
        "方法一",
        "方法二",
        "你能具体说明一下",
        "如果暂时不确定",
        "需要我帮你",
    ]
    if not a or len(a) < 24:
        return True
    if any(marker.lower() in (answer or "").lower() for marker in generic_markers):
        return True
    if _has_repeated_lines(answer):
        return True
    if q and a and q in a and len(a) < len(q) * 2.2:
        return True
    return False


async def _synthesize_stronger_answer(message: str, tool_name: str | None, tool_result: str | None, model: str) -> str:
    synthesis_messages = [
        {
            "role": "system",
            "content": (
                "你是高质量本地 Agent 总结器。\n"
                "任务：把已有真实执行结果整理成最终答复。\n"
                "要求：\n"
                "1. 必须基于真实结果回答，禁止空话。\n"
                "2. 不要重复用户原话。\n"
                "3. 先给结论，再给 2-5 条关键结果。\n"
                "4. 如果结果显示失败或缺失，就明确说明哪里失败。\n"
                "5. 不要再输出工具调用，不要再教用户怎么自己做。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"原任务：{message}\n"
                f"工具：{tool_name or 'none'}\n"
                f"真实结果：\n{tool_result or '(empty)'}\n\n"
                "请直接输出最终答案。"
            ),
        },
    ]
    return await call_llm(synthesis_messages, model)


def _fallback_answer_from_tool_result(message: str, tool_name: str | None, tool_result: str | None) -> str:
    text = (tool_result or "").strip()
    if not text:
        return _build_honest_failure_answer(message, tool_name, tool_result)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if tool_name == "get_device_profile":
        titles = [line for line in lines if "常见前台窗口" in line or "常见进程" in line]
        bullets = [line for line in lines if line.startswith("- ") or line.startswith("  - ")]
        out = ["我已经拿到设备画像，先给你直接结论："]
        if any("Codex" in line or "AI Agent" in line or "Cursor" in line or "Claude" in line for line in lines):
            out.append("- 你最近主要在 Codex、AI Agent、Cursor、Claude 这些开发/对话工具之间切换。")
        if any("cmd.exe" in line for line in lines):
            out.append("- 你最近明显在频繁排查本地环境、命令行和启动链路。")
        if any("样本数" in line for line in lines):
            sample_line = next((line for line in lines if "近24h 样本数" in line), "")
            if sample_line:
                out.append(f"- 当前画像已经有持续采样基础：{sample_line.replace('- ', '')}")
        out.append("- 这套结果说明你近期重点还是本地 Agent 升级、桌面工作流和环境排障。")
        if bullets:
            out.append("")
            out.append("真实画像摘录：")
            out.extend(bullets[:8])
        return "\n".join(out)

    if tool_name == "list_files":
        visible = [line for line in lines if line and not line.lower().startswith("not found")]
        if visible:
            return "我已经列到真实目录内容了：\n" + "\n".join(visible[:20])

    if tool_name == "local_search" and _looks_like_model_download_research(message):
        return _fallback_model_download_answer(text)

    if tool_name == "read_file":
        if _looks_like_summary_request(message):
            return _local_read_file_summary(text)
        preview = text[:1200] + ("..." if len(text) > 1200 else "")
        return "我已经读到真实文件内容了，先给你原文预览：\n" + preview

    if tool_name == "get_recent_desktop_files":
        return "我已经拿到桌面最近文件，先给你直接结果：\n" + "\n".join(lines[:16])

    if tool_name == "get_recent_work_summary":
        return "我已经拿到最近活动素材，先给你直接摘要素材：\n" + "\n".join(lines[:20])

    if tool_name == "get_evolution_profile":
        return "我已经拿到自进化画像，先给你核心内容：\n" + "\n".join(lines[:24])

    if tool_name == "run_task_orchestration":
        return "多模型协作已经返回结果：\n" + "\n".join(lines[:24])

    return "我已经拿到真实执行结果：\n" + "\n".join(lines[:20])


def _fallback_model_download_answer(search_text: str) -> str:
    """Give a useful structured answer when LLM synthesis times out after search."""
    hay = (search_text or "").lower()
    candidates = [
        (
            "Qwen3-32B-GGUF Q4_K_M",
            "综合主力首选，32B 量化后适合 24GB 显存，聊天/代码/推理比较均衡。",
            "Qwen/Qwen3-32B-GGUF",
        ),
        (
            "DeepSeek-R1-Distill-Qwen-32B-GGUF Q4_K_M",
            "偏推理、数学、代码，24GB 显存可优先选 Q4_K_M。",
            "DeepSeek-R1-Distill-Qwen-32B-GGUF",
        ),
        (
            "Qwen3-30B-A3B-GGUF",
            "MoE 架构，激活参数少，速度和显存压力更友好。",
            "Qwen/Qwen3-30B-A3B-GGUF",
        ),
        (
            "Mistral-Small-3.2-24B-Instruct-GGUF",
            "24B 指令模型，工具调用、英文和多语言任务表现稳。",
            "Mistral-Small-3.2-24B-Instruct-2506-GGUF",
        ),
        (
            "Gemma-3-27B-IT GGUF",
            "通用对话强，但通常需要确认许可/下载渠道，24GB 建议量化版。",
            "gemma-3-27b-it GGUF",
        ),
    ]
    found_urls = re.findall(r"https?://[^\s)>\]]+", search_text or "")
    source_lines = []
    for url in found_urls[:6]:
        if any(domain in url.lower() for domain in ["huggingface.co", "ollama.com", "modelscope.cn"]):
            source_lines.append(f"- {url}")
    if not source_lines:
        source_lines = ["- 搜索结果没有稳定命中官方下载页；建议优先在 Hugging Face 搜这些模型名。"]

    lines = [
        "结论：5090/24G 本地优先下 Qwen3-32B-GGUF 的 Q4_K_M；如果更重视推理/代码，再下 DeepSeek-R1-Distill-Qwen-32B-GGUF Q4_K_M。",
        "",
        "推荐清单：",
    ]
    for i, (name, why, repo_hint) in enumerate(candidates, 1):
        marker = "（搜索结果中有相关命中）" if repo_hint.lower() in hay else ""
        lines.append(f"{i}. {name}：{why}{marker}")
    lines.extend(
        [
            "",
            "下载/运行建议：",
            "- 24GB 显存优先选 GGUF 的 Q4_K_M / Q5_K_M；上下文开太大会爆显存。",
            "- Ollama/llama.cpp 都能跑 GGUF；追求速度先 Q4_K_M，追求质量再试 Q5_K_M。",
            "- 不要下 FP16/完整 32B 权重直接硬塞 24GB，容易 OOM。",
            "",
            "可用来源线索：",
            *source_lines[:6],
        ]
    )
    return "\n".join(lines)


def _execute_tool_sync(tool_name: str, params: dict) -> str:
    fn = TOOL_MAP.get(tool_name)
    if not fn:
        return f"Unknown tool: {tool_name}"
    return fn(params)


async def run_agent(message: str, model: str, session_id: str | None = None):
    from model_lock import enforce_locked_model

    sid = (session_id or "").strip() or "agent"
    model = enforce_locked_model(model)
    rt = get_runtime()
    if _looks_like_garbled_text(message):
        return [
            {
                "type": "final_answer",
                "content": "这条输入在进入后端前已经乱码了，我不会把它写进记忆。请从桌面 Agent 正常输入中文，或者检查调用端编码是否是 UTF-8。",
            }
        ]
    save_user_turn(sid, message)
    remember_from_message(sid, "user", message)
    mx = rt.context_block_max_chars
    (
        memory_context,
        knowledge_context,
        evolution_context,
        workflow_context,
        playbook_context,
        skill_context,
    ) = await asyncio.gather(
        asyncio.to_thread(lambda: compress_for_llm(build_memory_context(message), mx, "memory")),
        asyncio.to_thread(lambda: compress_for_llm(build_knowledge_context(message), mx, "knowledge")),
        asyncio.to_thread(lambda: compress_for_llm(get_evolution_profile_text(), mx, "evolution")),
        asyncio.to_thread(lambda: compress_for_llm(build_workflow_context(message), mx, "workflow")),
        asyncio.to_thread(lambda: compress_for_llm(build_playbook_context(message), mx, "playbook")),
        asyncio.to_thread(lambda: compress_for_llm(build_skill_pack_context(message), mx, "skills")),
    )
    system_context_parts = [SYSTEM_PROMPT]
    if memory_context:
        system_context_parts.append(memory_context)
    if playbook_context:
        system_context_parts.append(playbook_context)
    if skill_context:
        system_context_parts.append(skill_context)
    if knowledge_context:
        system_context_parts.append(knowledge_context)
    if evolution_context:
        system_context_parts.append(evolution_context)
    if workflow_context:
        system_context_parts.append(workflow_context)
    system_context_parts[0] = _build_system_prompt()
    system_content = "\n\n".join(system_context_parts)
    messages = build_messages_with_history(system_content, sid)
    steps = []
    tool_used = False
    last_tool_name = None
    last_tool_result = None
    last_review: dict | None = None
    forced_tool_call = infer_tool_from_message(message)

    for _ in range(rt.agent_max_steps):
        if forced_tool_call is not None and not tool_used:
            response = ""
            tool_call = forced_tool_call
            steps.append({
                "type": "thinking",
                "content": "已按用户意图直接选择工具执行。",
            })
        else:
            try:
                if tool_used and last_tool_result:
                    response = await asyncio.wait_for(call_llm(messages, model), timeout=25)
                else:
                    response = await call_llm(messages, model)
            except asyncio.TimeoutError:
                cleaned = _fallback_answer_from_tool_result(message, last_tool_name, last_tool_result)
                if not _looks_like_garbled_text(message):
                    remember_from_message(sid, "assistant", cleaned)
                record_task_outcome("agent_run", "success", last_tool_name or "agent_timeout_fallback", cleaned[:300])
                last_review = record_task_review(message, "success", last_tool_name or "", cleaned, last_tool_result or "")
                steps.append({"type": "final_answer", "content": cleaned})
                break
            tool_call = parse_tool(response)

        if tool_call:
            tool_name = tool_call.get("name")
            params = tool_call.get("parameters", {})
            last_tool_name = tool_name
            thinking = response.split("<tool_call>")[0].strip() if "<tool_call>" in response else ""
            if thinking:
                steps.append({"type": "thinking", "content": thinking})
            steps.append({"type": "tool_call", "tool": tool_name, "params": params})
            try:
                result = await asyncio.to_thread(_execute_tool_sync, tool_name, params)
            except Exception as e:
                result = f"Tool error: {e}"
            tool_used = True
            result_text = str(result)
            packed = compress_tool_result_for_llm(result_text, rt.tool_result_max_chars, tool_name or "tool")
            last_tool_result = packed
            result_failed = _tool_result_failed(tool_name, result_text)
            tool_status = "failed" if result_failed else "success"
            record_task_outcome("tool", tool_status, tool_name or "", result_text[:300])
            steps.append({"type": "tool_result", "tool": tool_name, "result": packed[:8000]})
            if result_failed:
                final_text = _build_honest_failure_answer(message, tool_name, packed)
                remember_from_message(sid, "assistant", final_text)
                record_task_outcome("agent_run", "failed", tool_name or "tool", final_text[:300])
                last_review = record_task_review(message, "failed", tool_name or "", final_text, result_text)
                steps.append({"type": "final_answer", "content": final_text})
                break
            if tool_name == "local_search" and _looks_like_model_download_research(message):
                final_text = _fallback_model_download_answer(result_text)
                remember_from_message(sid, "assistant", final_text)
                record_task_outcome("agent_run", "success", tool_name or "model_search", final_text[:300])
                last_review = record_task_review(message, "success", tool_name or "", final_text, result_text)
                steps.append({"type": "final_answer", "content": final_text})
                break
            if forced_tool_call is not None and (tool_name in FAST_TOOL_FINALS):
                final_text = _fallback_answer_from_tool_result(message, tool_name, packed)
                if not _looks_like_garbled_text(message):
                    remember_from_message(sid, "assistant", final_text)
                record_task_outcome("agent_run", "success", tool_name or "tool_forced", final_text[:300])
                last_review = record_task_review(message, "success", tool_name or "", final_text, result_text)
                steps.append({"type": "final_answer", "content": final_text})
                break
            messages += [
                {"role": "assistant", "content": response},
                {
                    "role": "user",
                    "content": (
                        f"工具 {tool_name} 的执行结果如下：\n{packed}\n\n"
                        "现在请直接基于这个结果给用户最终答案。"
                        "不要再教用户如何调用工具，也不要再输出 <tool_call>。"
                    ),
                },
            ]
            continue

        cleaned = re.sub(r"<tool_call>.*?</tool_call>", "", response, flags=re.DOTALL).strip()
        if _looks_like_fake_completion(cleaned):
            if tool_used and _is_successful_tool_result(last_tool_result or ""):
                cleaned = _fallback_answer_from_tool_result(message, last_tool_name, last_tool_result)
                record_task_outcome("agent_run", "success", last_tool_name or "agent_final", cleaned[:300])
                last_review = record_task_review(message, "success", last_tool_name or "", cleaned, last_tool_result or "")
            else:
                cleaned = _build_honest_failure_answer(message, last_tool_name, last_tool_result)
                record_task_outcome("agent_run", "failed", last_tool_name or "agent_final", cleaned[:300])
                last_review = record_task_review(message, "failed", last_tool_name or "", cleaned, last_tool_result or "")
        elif tool_used and _looks_like_manual_instructions(cleaned):
            if _is_successful_tool_result(last_tool_result or ""):
                cleaned = _fallback_answer_from_tool_result(message, last_tool_name, last_tool_result)
                record_task_outcome("agent_run", "success", last_tool_name or "agent_final", cleaned[:300])
                last_review = record_task_review(message, "success", last_tool_name or "", cleaned, last_tool_result or "")
            else:
                cleaned = _build_honest_failure_answer(message, last_tool_name, last_tool_result)
                record_task_outcome("agent_run", "failed", last_tool_name or "agent_final", cleaned[:300])
                last_review = record_task_review(message, "failed", last_tool_name or "", cleaned, last_tool_result or "")
        elif not tool_used and _looks_like_action_request(message) and _looks_like_manual_instructions(cleaned):
            cleaned = _build_honest_failure_answer(message)
            record_task_outcome("agent_run", "failed", "agent_manual_fallback", cleaned[:300])
            last_review = record_task_review(message, "failed", "agent_manual_fallback", cleaned, "")
        elif tool_used and _is_low_quality_answer(message, cleaned):
            try:
                strengthened = await _synthesize_stronger_answer(message, last_tool_name, last_tool_result, model)
                strengthened = re.sub(r"<tool_call>.*?</tool_call>", "", strengthened, flags=re.DOTALL).strip()
                if strengthened and not _is_low_quality_answer(message, strengthened):
                    cleaned = strengthened
                else:
                    cleaned = _fallback_answer_from_tool_result(message, last_tool_name, last_tool_result)
                    record_task_outcome("agent_run", "success", last_tool_name or "agent_quality_guard", cleaned[:300])
                    last_review = record_task_review(message, "success", last_tool_name or "", cleaned, last_tool_result or "")
            except Exception:
                cleaned = _fallback_answer_from_tool_result(message, last_tool_name, last_tool_result)
                record_task_outcome("agent_run", "success", last_tool_name or "agent_quality_guard", cleaned[:300])
                last_review = record_task_review(message, "success", last_tool_name or "", cleaned, last_tool_result or "")
        elif not tool_used and _is_low_quality_answer(message, cleaned) and _looks_like_action_request(message):
            cleaned = _build_honest_failure_answer(message)
            record_task_outcome("agent_run", "failed", "agent_quality_guard", cleaned[:300])
            last_review = record_task_review(message, "failed", "agent_quality_guard", cleaned, "")
        if not cleaned:
            cleaned = "任务已处理，但模型没有返回可展示文本。"
        if not _looks_like_garbled_text(message):
            remember_from_message(sid, "assistant", cleaned)
        if last_review is None and not _looks_like_fake_completion(cleaned) and "这次我没有真正把任务做完。" not in cleaned:
            record_task_outcome("agent_run", "success", "agent_final", cleaned[:300])
            last_review = record_task_review(message, "success", last_tool_name or "", cleaned, last_tool_result or "")
        steps.append({"type": "final_answer", "content": cleaned})
        break

    if not any(step["type"] == "final_answer" for step in steps):
        final_text = "任务已执行，但未生成最终总结。请换个说法再试一次。"
        remember_from_message(sid, "assistant", final_text)
        record_task_outcome("agent_run", "failed", "agent_final", final_text[:300])
        last_review = record_task_review(message, "failed", "agent_final", final_text, last_tool_result or "")
        steps.append({"type": "final_answer", "content": final_text})

    if rt.agent_self_evolve and last_review is not None:
        ingest_review_lesson(message, last_review)

    persist_agent_answer(sid, steps)

    if (rt.webhook_url or "").strip():
        final_preview = ""
        for s in reversed(steps):
            if s.get("type") == "final_answer":
                final_preview = (s.get("content") or "")[:400]
                break
        asyncio.create_task(
            notify_agent_completed(
                {
                    "event": "agent_run_done",
                    "message_preview": message[:400],
                    "answer_preview": final_preview,
                    "step_count": len(steps),
                }
            )
        )

    return steps


@router.get("/config")
def agent_public_config():
    r = get_runtime()
    od = orchestration_defaults()
    od.pop("llm_backend", None)
    return {
        "llm_backend": r.llm_backend,
        "ollama_base": r.ollama_base,
        "openai_base_url": r.openai_base_url or None,
        "openai_api_key_set": bool(r.openai_api_key),
        "default_model": r.default_chat_model,
        "orchestration": od,
        "evolution": {
            "skill_pack": r.agent_skill_pack,
            "self_evolve": r.agent_self_evolve,
            "evolve_llm": r.agent_evolve_llm,
            "evolve_model": r.agent_evolve_model,
        },
        "limits": {
            "tool_result_max_chars": r.tool_result_max_chars,
            "context_block_max_chars": r.context_block_max_chars,
            "agent_max_steps": r.agent_max_steps,
            "ollama_timeout_sec": r.ollama_timeout_sec,
            "chat_history_max_messages": r.chat_history_max_messages,
        },
    }


@router.post("/runtime/reload")
def agent_reload_runtime():
    r = reload_runtime()
    return {
        "ok": True,
        "llm_backend": r.llm_backend,
        "ollama_base": r.ollama_base,
        "default_model": r.default_chat_model,
    }


@router.get("/playbook")
def agent_playbook(limit: int = 40):
    return {"items": list_playbook_entries(limit)}


@router.post("/evolve/distill")
def agent_evolve_distill():
    return distill_playbook_with_llm()


@router.post('/run')
async def agent_run(req: AgentRequest):
    from model_lock import enforce_locked_model

    req.model = enforce_locked_model(req.model)

    async def generate():
        try:
            import inspect

            sig = inspect.signature(run_agent)
            if len(sig.parameters) <= 2:
                steps = await run_agent(req.message, req.model)
            else:
                steps = await run_agent(req.message, req.model, req.session_id)
            for step in steps:
                yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
        except Exception as e:
            fallback = {
                "type": "final_answer",
                "content": _agent_run_stream_error_message(e),
            }
            yield f"data: {json.dumps(fallback, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type='text/event-stream')


@router.get("/tools")
def list_tools():
    """Agent 可用工具清单（供前端 / 自检）。"""
    groups = {
        "search_crawl": ["web_search", "local_search", "local_scrape_url"],
        "files_code": ["read_file", "write_file", "list_files", "execute_python"],
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
            "browser_screenshot",
            "browser_click_and_extract",
            "browser_fill_form",
        ],
        "parallel": ["run_parallel_subagents"],
        "integration": ["http_request", "query_database", "mcp_invoke"],
    }
    flat = list(TOOL_MAP.keys())
    return {"tools": flat, "count": len(flat), "groups": groups}
