"""Inbound messaging gateway stub (Telegram / Discord / Slack / generic webhook)."""

from __future__ import annotations

import hmac
import os
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent_runtime import get_runtime

router = APIRouter()


class InboundMessage(BaseModel):
    channel: str = Field("generic", description="telegram | discord | slack | generic")
    text: str
    user_id: str = ""
    session_id: str | None = None
    mode: str = Field("agent", description="agent | chat")
    model: str | None = None
    reply_webhook: str | None = Field(None, description="POST 结果 JSON 到此 URL")


def _gateway_enabled() -> bool:
    return os.environ.get("GATEWAY_ENABLED", "1").strip() not in ("0", "false", "off")


def _check_token(channel: str, token: str | None) -> None:
    if not _gateway_enabled():
        raise HTTPException(503, "gateway disabled (GATEWAY_ENABLED=0)")
    secret = (os.environ.get("GATEWAY_SECRET") or "").strip()
    # hmac.compare_digest 做常量时间比较，防止计时攻击通过响应延迟推断 secret 内容
    if secret and not hmac.compare_digest(token or "", secret):
        raise HTTPException(401, "invalid gateway token")
    allow = os.environ.get("GATEWAY_CHANNELS", "telegram,discord,slack,generic")
    allowed = {x.strip().lower() for x in allow.split(",") if x.strip()}
    if channel.lower() not in allowed:
        raise HTTPException(400, f"channel not allowed: {channel}")


@router.get("/status")
def gateway_status():
    return {
        "ok": True,
        "enabled": _gateway_enabled(),
        "channels": (os.environ.get("GATEWAY_CHANNELS") or "telegram,discord,slack,generic").split(","),
        "secret_required": bool((os.environ.get("GATEWAY_SECRET") or "").strip()),
    }


@router.post("/inbound")
async def gateway_inbound(body: InboundMessage, token: str | None = None):
    _check_token(body.channel, token)
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "empty text")
    from model_lock import enforce_locked_model

    rt = get_runtime()
    model = enforce_locked_model((body.model or "").strip() or rt.default_chat_model)
    sid = (body.session_id or "").strip() or f"gw-{body.channel}-{body.user_id or 'anon'}-{uuid.uuid4().hex[:8]}"
    mode = (body.mode or "agent").strip().lower()
    result_text = ""

    if mode == "chat":
        from chat import save_message
        from llm_client import chat_complete_async

        messages = [{"role": "user", "content": text}]
        result_text = await chat_complete_async(messages, model)
        save_message(sid, "user", text)
        save_message(sid, "assistant", result_text)
    else:
        from agent import run_agent

        steps = await run_agent(text, model)  # run_agent 返回 list，不是 AsyncGenerator
        final = next((s for s in reversed(steps) if s.get("type") == "final_answer"), None)
        result_text = (final or {}).get("content") or ""

    payload: dict[str, Any] = {
        "ok": True,
        "channel": body.channel,
        "session_id": sid,
        "mode": mode,
        "reply": result_text[:12000],
    }

    reply_url = (body.reply_webhook or os.environ.get("GATEWAY_REPLY_WEBHOOK") or "").strip()
    if reply_url:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                await client.post(reply_url, json=payload)
        except Exception as e:
            payload["reply_webhook_error"] = str(e)

    return payload


@router.post("/telegram")
async def telegram_webhook(update: dict, token: str | None = None):
    """最小 Telegram 兼容：从 update.message.text 取用户话。"""
    _check_token("telegram", token)
    msg = (update.get("message") or update.get("edited_message") or {})
    text = (msg.get("text") or "").strip()
    chat = msg.get("chat") or {}
    user = msg.get("from") or {}
    if not text:
        return {"ok": False, "hint": "no text in update"}
    inbound = InboundMessage(
        channel="telegram",
        text=text,
        user_id=str(user.get("id") or chat.get("id") or ""),
        session_id=f"tg-{chat.get('id')}",
    )
    return await gateway_inbound(inbound, token=token)
