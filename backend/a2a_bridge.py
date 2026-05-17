"""Minimal A2A-style shim: agent card + single-turn message:send -> run_agent."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agent_runtime import get_runtime

router = APIRouter()


@router.get("/v1/agent-card")
def agent_card():
    r = get_runtime()
    return {
        "name": "local-fastapi-agent",
        "description": "Tool-use agent with memory, orchestration, and optional webhooks.",
        "default_model": r.default_chat_model,
        "llm_backend": r.llm_backend,
        "protocol": "a2a-lite-shim",
        "capabilities": ["tools", "memory", "orchestration"],
    }


class A2AMessage(BaseModel):
    message: str = Field("", max_length=500_000)
    text: str | None = Field(None, max_length=500_000)
    model: str | None = None


@router.post("/v1/message:send")
async def message_send(body: A2AMessage):
    text = ((body.text or body.message) or "").strip()
    if not text:
        return {"ok": False, "error": "empty message"}
    from agent import run_agent

    rt = get_runtime()
    model = (body.model or rt.default_chat_model or "").strip()
    steps = await run_agent(text, model)
    final = ""
    for s in reversed(steps):
        if s.get("type") == "final_answer":
            final = s.get("content") or ""
            break
    return {"ok": True, "model": model, "final_answer": final, "steps": steps}
