"""Agent 内调用 MCP 桥（builtin 或 MCP_SERVERS 远程）。"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx


def _remote_servers() -> list[dict[str, Any]]:
    raw = (os.environ.get("MCP_SERVERS") or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def mcp_invoke(server: str, tool: str, arguments: dict[str, Any] | None = None) -> str:
    server = (server or "builtin").strip()
    tool = (tool or "").strip()
    args = arguments if isinstance(arguments, dict) else {}
    if not tool:
        return "mcp_invoke error: 缺少 tool 名称"

    if server in ("builtin", "local", ""):
        from agent import TOOL_MAP, _normalize_parsed_tool

        norm = _normalize_parsed_tool({"name": tool, "parameters": args})
        fn = TOOL_MAP.get(norm.get("name") or tool)
        if not fn:
            return f"mcp_invoke error: unknown builtin tool {tool}"
        try:
            return str(fn(norm.get("parameters") or args))[:16000]
        except Exception as e:
            return f"mcp_invoke error: {e}"

    for srv in _remote_servers():
        if (srv.get("name") or "") != server:
            continue
        base = (srv.get("url") or "").rstrip("/")
        if not base:
            return f"mcp_invoke error: server {server} has no url"
        headers = {}
        if srv.get("api_key"):
            headers["Authorization"] = f"Bearer {srv['api_key']}"
        try:
            with httpx.Client(timeout=float(srv.get("timeout", 120))) as client:
                r = client.post(f"{base}/tools/call", json={"name": tool, "arguments": args}, headers=headers)
                r.raise_for_status()
                return json.dumps(r.json(), ensure_ascii=False)[:16000]
        except Exception as e:
            return f"mcp_invoke error: {e}"
    return f"mcp_invoke error: unknown server {server}"
