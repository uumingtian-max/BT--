"""HTTP：单一语音通道（灵光 Edge TTS）+ 可进化档案。"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from lingguang_tts import (
    DEFAULT_VOICE,
    health_status,
    normalize_request_text,
    resolve_voice,
    synthesize_mp3_async,
)
from voice_profile import apply_patch, load_profile, maybe_evolve_from_habit, public_status

router = APIRouter(tags=["voice"])


class TTSRequest(BaseModel):
    text: str = Field(default="", max_length=4000)
    text_b64: str = Field(
        default="",
        description="UTF-8 文本的 base64；PowerShell 发中文乱码时用此字段",
    )
    voice: str = ""


class VoiceEvolveRequest(BaseModel):
    startup_text: str | None = None
    voice: str | None = None
    short_ack: str | None = None
    reason: str = "api"


async def _synthesize_response(text: str, voice: str | None) -> Response | JSONResponse:
    try:
        cleaned = normalize_request_text(text, "")
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
    if not cleaned:
        return JSONResponse(status_code=400, content={"ok": False, "error": "text is empty"})
    voice_id = resolve_voice(voice) if voice else resolve_voice(load_profile().get("voice"))
    data, err = await synthesize_mp3_async(cleaned, voice_id)
    if err:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": err,
                "voice": voice_id,
                "text_preview": cleaned[:80],
                "text_len": len(cleaned),
            },
        )
    return Response(content=data, media_type="audio/mpeg")


@router.get("/voice/health")
async def voice_health():
    return health_status()


@router.get("/voice/profile")
async def voice_profile():
    return public_status()


@router.post("/voice/evolve")
async def voice_evolve(req: VoiceEvolveRequest):
    patch: dict = {}
    if req.startup_text is not None:
        patch["startup_text"] = req.startup_text.strip()
    if req.voice is not None:
        patch["voice"] = req.voice.strip()
    if req.short_ack is not None:
        patch["short_ack"] = req.short_ack.strip()
    if not patch:
        return JSONResponse(status_code=400, content={"ok": False, "error": "no patch fields"})
    prof = apply_patch(patch, reason=req.reason or "api")
    return {"ok": True, "profile": public_status(), "saved": prof.get("generation")}


@router.post("/voice/startup")
async def voice_startup():
    """开机/进应用播报：文案来自 voice_profile（可进化）。"""
    prof = load_profile()
    if not prof.get("startup_on_boot"):
        return Response(status_code=204)
    text = str(prof.get("startup_text") or "黑光已就位，等待指令")
    return await _synthesize_response(text, str(prof.get("voice") or DEFAULT_VOICE))


@router.post("/voice/speak")
async def voice_speak(req: TTSRequest):
    """通用播报；未传 voice 时用档案默认。"""
    try:
        text = normalize_request_text(req.text, req.text_b64)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
    voice = req.voice.strip() if req.voice else str(load_profile().get("voice") or DEFAULT_VOICE)
    return await _synthesize_response(text, voice)


@router.post("/edge_tts")
async def edge_tts_endpoint(req: TTSRequest):
    """兼容旧路径；行为同 /voice/speak。"""
    return await voice_speak(req)
