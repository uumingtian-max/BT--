#!/usr/bin/env python3
"""ONYX-OVERRIDE 全工具实机演练：真实调用 TOOL_MAP + HTTP /mcp/call。"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKEND))
os.environ.setdefault("REQUEST_LOG", "0")
if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(
        Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
    )

from env_bootstrap import load_backend_dotenv  # noqa: E402

load_backend_dotenv()


def effective_llm_backend() -> str:
    """与 agent_runtime.get_runtime 一致：有 OPENAI_BASE_URL 才走网关。"""
    raw = os.environ.get("LLM_BACKEND", "ollama").strip().lower()
    oa = os.environ.get("OPENAI_BASE_URL", "").strip()
    if raw in ("openai", "openai_compatible", "vllm", "litellm", "localai") and oa:
        return "openai_compatible"
    return "ollama"


def wait_for_llm_gateway() -> None:
    """按 backend/.env 等待推理可用；默认推荐 Ollama（Windows GPU 稳），网关模式需自备 vLLM/LM Studio。"""
    import httpx

    mode = effective_llm_backend()
    wait_sec = int(os.environ.get("LLM_WAIT_SEC", "120"))
    steps = max(3, wait_sec // 5)

    if mode == "ollama":
        base = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        for i in range(steps):
            try:
                r = httpx.get(f"{base}/api/tags", timeout=6.0)
                if r.status_code == 200:
                    print(f"[live] Ollama 就绪 ({base})", flush=True)
                    return
            except Exception:
                pass
            if i == 0:
                print(f"[live] 等待 Ollama ({base})…", flush=True)
            time.sleep(5)
        raise SystemExit(
            "Ollama 未就绪。请先安装并运行 Ollama，或使用 backend\\.env.example 的稳定配置。"
        )

    base = os.environ["OPENAI_BASE_URL"].strip().rstrip("/")
    url = base if base.endswith("/v1") else f"{base}/v1"
    for i in range(steps):
        try:
            r = httpx.get(f"{url}/models", timeout=10.0)
            data = r.json().get("data") if r.status_code == 200 else []
            if data:
                print(f"[live] OpenAI 兼容网关就绪 ({url})", flush=True)
                return
        except Exception:
            pass
        if i == 0:
            print(
                "[live] 等待网关…（Windows 原生 vLLM GPU 不可靠；日常请改用 LLM_BACKEND=ollama）",
                flush=True,
            )
        time.sleep(5)
    raise SystemExit(
        f"网关未就绪 ({url})。请先在 GPU 可用的环境启动 vLLM/LM Studio，或改回 Ollama：复制 backend\\.env.example 为 .env"
    )


wait_for_llm_gateway()

import agent_runtime  # noqa: E402

agent_runtime.get_runtime.cache_clear()

from agent import TOOL_MAP  # noqa: E402

REPORT = LOG_DIR / f"tools-live-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
TMP_WRITE = ROOT / "outputs" / "_tool_smoke_write.txt"
TMP_WRITE.parent.mkdir(parents=True, exist_ok=True)
MAIN_PY = BACKEND / "main.py"
MEMORY_DB = BACKEND / "memory.db"
QUICK = os.environ.get("TOOL_LIVE_QUICK", "").strip().lower() in ("1", "true", "yes", "on")


def resolve_default_model() -> str:
    import httpx

    backend = effective_llm_backend()
    if backend == "openai_compatible":
        base = (os.environ.get("OPENAI_BASE_URL") or "http://127.0.0.1:8001/v1").rstrip("/")
        try:
            r = httpx.get(f"{base}/models", timeout=3.0)
            if r.status_code == 200:
                data = r.json().get("data") or []
                if data and isinstance(data[0], dict) and data[0].get("id"):
                    return str(data[0]["id"])
        except Exception:
            pass
        return os.environ.get("AGENT_DEFAULT_MODEL", "nvidia/Gemma-4-26B-A4B-NVFP4")
    return os.environ.get("AGENT_DEFAULT_MODEL", "qwen3:14b")


DEFAULT_MODEL = resolve_default_model()


def _looks_error(name: str, text: str) -> bool:
    low = (text or "").lower()
    if low.startswith(f"{name} error"):
        return True
    if f"{name} error:" in low[:200]:
        return True
    return False


def run_tool(name: str, params: dict, *, expect_error: bool = False) -> dict:
    t0 = time.perf_counter()
    try:
        out = TOOL_MAP[name](params)
        text = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)[:8000]
        elapsed = round(time.perf_counter() - t0, 2)
        err = _looks_error(name, text)
        if name == "generate_image" and '"status": "success"' in text and "placeholder" in text:
            err = False
        ok = err if expect_error else not err
        return {"tool": name, "ok": ok, "elapsed_sec": elapsed, "preview": text[:600], "expect_error": expect_error}
    except Exception as e:
        return {
            "tool": name,
            "ok": False,
            "elapsed_sec": round(time.perf_counter() - t0, 2),
            "preview": str(e),
            "trace": traceback.format_exc()[-600:],
        }


def http_mcp(tool: str, arguments: dict) -> dict:
    import urllib.request

    t0 = time.perf_counter()
    body = json.dumps({"server": "builtin", "tool": tool, "arguments": arguments}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/mcp/call",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "tool": f"mcp:{tool}",
            "ok": bool(data.get("ok")),
            "elapsed_sec": round(time.perf_counter() - t0, 2),
            "preview": str(data.get("result", data))[:600],
        }
    except Exception as e:
        return {
            "tool": f"mcp:{tool}",
            "ok": False,
            "elapsed_sec": round(time.perf_counter() - t0, 2),
            "preview": str(e),
        }


def main() -> int:
    # (tool_name, params, expect_error)
    cases: list[tuple[str, dict, bool]] = [
        ("web_search", {"query": "latest local LLM tools 2026"}, False),
        ("local_search", {"query": "python", "limit": 2}, False),
        ("local_scrape_url", {"url": "not-a-url"}, True),
        ("local_scrape_url", {"url": "https://example.com", "max_chars": 2500}, False),
        ("read_file", {"path": str(MAIN_PY)}, False),
        ("write_file", {"path": str(TMP_WRITE), "content": f"smoke {datetime.now().isoformat()}\n"}, False),
        ("list_files", {"directory": str(ROOT / "backend" / "tools")}, False),
        ("execute_python", {"code": "print('tool_ok')"}, False),
        ("get_device_profile", {}, False),
        ("get_recent_desktop_files", {}, False),
        ("get_recent_work_summary", {}, False),
        ("get_evolution_profile", {}, False),
        ("notebook_ingest", {"title": "实机演练", "text": "alpha\nbeta"}, False),
        ("run_project_check", {"target": "backend"}, False),
        ("http_request", {"url": "https://httpbin.org/get", "method": "GET"}, False),
        (
            "query_database",
            {"path": str(MEMORY_DB), "sql": "SELECT name FROM sqlite_master WHERE type='table' LIMIT 5"},
            False,
        ),
        ("get_foreground_window", {}, False),
        ("list_windows", {"limit": 8}, False),
        ("focus_window", {"title": "__no_such_window_xyz__"}, True),
        ("send_hotkey", {"keys": ""}, True),
        ("type_text", {"text": ""}, True),
        ("open_url", {"url": "ftp://bad"}, True),
        ("open_path", {"path": "__missing_xyz__"}, True),
        ("click_screen", {"x": 5, "y": 5}, False),
        ("browser_navigate", {"url": "https://example.com", "wait_ms": 1200}, False),
        (
            "browser_screenshot",
            {"url": "https://example.com", "output_path": "outputs/tool_smoke_browser.png"},
            False,
        ),
        ("browser_fill_form", {"fields": {}}, True),
        (
            "browser_click_and_extract",
            {"url": "https://example.com", "selector": "h1", "extract_selector": "h1"},
            False,
        ),
        ("mcp_invoke", {"server": "builtin", "tool": "execute_python", "arguments": {"code": "print(42)"}}, False),
        ("generate_image", {"prompt": "small blue circle", "output_path": "outputs/tool_smoke_sd.png"}, False),
        ("generate_video", {"image_paths": []}, True),
        ("text_to_speech", {"text": "好", "output_path": "outputs/tool_smoke_tts.wav"}, False),
    ]
    if not QUICK:
        cases.extend(
            [
                ("run_parallel_subagents", {"tasks": ["只回复：好"], "model": DEFAULT_MODEL}, False),
                ("run_task_orchestration", {"message": "用一句话回答：2+2等于几"}, False),
                ("notebook_synthesize", {"title": "短测", "text": "实机材料一行"}, False),
            ]
        )

    mode = "快速" if QUICK else "完整"
    print(f"\n=== ONYX-OVERRIDE 实机演练 [{mode}] model={DEFAULT_MODEL} ({len(cases)} 项) ===\n", flush=True)
    results: list[dict] = []
    for name, params, expect_err in cases:
        print(f"  [{name}]", flush=True)
        r = run_tool(name, params, expect_error=expect_err)
        results.append(r)
        tag = "OK" if r["ok"] else "FAIL"
        prev = (r.get("preview") or "").replace("\n", " ")[:90]
        print(f"       {tag} {r['elapsed_sec']}s | {prev}", flush=True)

    print("\n=== HTTP /mcp/call ===\n", flush=True)
    for tool, args in [
        ("execute_python", {"code": "print('mcp_ok')"}),
        ("local_search", {"query": "agent", "limit": 1}),
    ]:
        print(f"  [mcp:{tool}]", flush=True)
        r = http_mcp(tool, args)
        results.append(r)
        print(f"       {'OK' if r['ok'] else 'FAIL'} {r['elapsed_sec']}s | {(r.get('preview') or '')[:90]}", flush=True)

    ok_n = sum(1 for r in results if r.get("ok"))
    fail = [r for r in results if not r.get("ok")]
    summary = {
        "time": datetime.now().isoformat(),
        "total": len(results),
        "ok": ok_n,
        "fail": len(fail),
        "failed": fail,
        "results": results,
    }
    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== 总结 {ok_n}/{len(results)} 通过 ===", flush=True)
    print(f"报告: {REPORT}", flush=True)
    if fail:
        print("失败:", ", ".join(r["tool"] for r in fail), flush=True)
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
