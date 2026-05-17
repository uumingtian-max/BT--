"""MCP-style tool bridge: builtin TOOL_MAP + optional HTTP MCP servers from env."""

from __future__ import annotations

import json
import os
import asyncio
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


def _mcp_enabled() -> bool:
    return os.environ.get("MCP_BRIDGE_ENABLED", "1").strip() not in (
        "0",
        "false",
        "off",
    )


def _load_remote_servers() -> list[dict[str, Any]]:
    raw = (os.environ.get("MCP_SERVERS") or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


@router.get("/status")
def mcp_status():
    return {
        "ok": True,
        "enabled": _mcp_enabled(),
        "remote_servers": [s.get("name") for s in _load_remote_servers()],
    }


@router.get("/tools")
def mcp_list_tools():
    from agent import TOOL_MAP

    if not _mcp_enabled():
        raise HTTPException(503, "MCP bridge disabled")
    builtin = sorted(TOOL_MAP.keys())
    remote = []
    for srv in _load_remote_servers():
        name = srv.get("name") or "unnamed"
        tools = srv.get("tools") or []
        remote.append({"server": name, "tools": tools})
    return {"ok": True, "builtin": builtin, "remote": remote}


class McpCallBody(BaseModel):
    server: str = Field("builtin", description="builtin 或 MCP_SERVERS 里的 name")
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


@router.post("/call")
async def mcp_call(body: McpCallBody):
    if not _mcp_enabled():
        raise HTTPException(503, "MCP bridge disabled")
    server = (body.server or "builtin").strip()
    tool = (body.tool or "").strip()
    args = body.arguments if isinstance(body.arguments, dict) else {}

    if server in ("builtin", "local", ""):
        from agent import TOOL_MAP, _normalize_parsed_tool

        norm = _normalize_parsed_tool({"name": tool, "parameters": args})
        fn = TOOL_MAP.get(norm.get("name") or tool)
        if not fn:
            raise HTTPException(404, f"unknown builtin tool: {tool}")
        try:
            result = await asyncio.to_thread(fn, norm.get("parameters") or args)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {
            "ok": True,
            "server": "builtin",
            "tool": tool,
            "result": str(result)[:16000],
        }

    for srv in _load_remote_servers():
        if (srv.get("name") or "") != server:
            continue
        base = (srv.get("url") or "").rstrip("/")
        if not base:
            raise HTTPException(400, f"server {server} has no url")
        headers = {}
        if srv.get("api_key"):
            headers["Authorization"] = f"Bearer {srv['api_key']}"
        payload = {"name": tool, "arguments": args}
        try:
            async with httpx.AsyncClient(timeout=float(srv.get("timeout", 120))) as client:
                r = await client.post(f"{base}/tools/call", json=payload, headers=headers)
                r.raise_for_status()
                return {"ok": True, "server": server, "tool": tool, "result": r.json()}
        except Exception as e:
            return {"ok": False, "server": server, "error": str(e)}

    raise HTTPException(404, f"unknown MCP server: {server}")
