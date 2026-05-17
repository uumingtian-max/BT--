"""Small local F5-TTS HTTP adapter for ONYX mobile voice replies.

Run this as a separate process after installing F5-TTS:
    python -m uvicorn backend.f5_tts_server:app --host 127.0.0.1 --port 9880

The main backend calls it through REAL_TTS_URL, so torch/F5 only load in this
optional process and the regular app can still start quickly.
"""

from __future__ import annotations

import io
import os
import re
import tempfile
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


app = FastAPI(title="ONYX F5-TTS Adapter", version="1.0.0")

_MODEL: Any | None = None
_MODEL_LOCK = threading.Lock()


def _load_backend_dotenv() -> None:
    path = Path(__file__).resolve().parent / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s = s[7:].strip()
        key, _, value = s.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_backend_dotenv()
_hf_endpoint = os.environ.get("F5_TTS_HF_ENDPOINT", "").strip()
if _hf_endpoint:
    os.environ["HF_ENDPOINT"] = _hf_endpoint
    os.environ["HUGGINGFACE_HUB_BASE_URL"] = _hf_endpoint


class F5TTSRequest(BaseModel):
    text: str = Field("", description="Text to synthesize")
    input: str = Field("", description="OpenAI-style alias for text")
    voice: str = Field("authorized", description="Voice id; currently informational")
    style: str = Field("", description="Style hint from ONYX")
    rate: str = "+0%"
    pitch: str = "+0Hz"
    format: str = "wav"
    ref_audio: str = Field("", description="Optional reference audio path")
    ref_audio_path: str = Field("", description="Alias for ref_audio")
    ref_text: str = Field("", description="Transcript of reference audio")
    seed: int | None = None


def _env_path(name: str) -> str:
    return os.environ.get(name, "").strip().strip('"')


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_ref_audio(body: F5TTSRequest) -> Path:
    raw = (body.ref_audio or body.ref_audio_path or _env_path("F5_TTS_REF_AUDIO")).strip()
    if not raw:
        raise HTTPException(
            status_code=400,
            detail="缺少 F5_TTS_REF_AUDIO。请配置一段你有授权的 3-10 秒参考音频。",
        )
    path = Path(raw)
    if not path.is_absolute():
        path = (_project_root() / path).resolve()
    if not path.is_file():
        raise HTTPException(status_code=400, detail=f"参考音频不存在: {path}")
    return path


def _ref_text(body: F5TTSRequest) -> str:
    text = (body.ref_text or os.environ.get("F5_TTS_REF_TEXT", "")).strip()
    return text


def _rate_to_speed(rate: str) -> float:
    match = re.search(r"([+-]?\d+)", str(rate or "0"))
    pct = int(match.group(1)) if match else 0
    pct = max(-30, min(30, pct))
    # F5 speed > 1 is faster. Keep the range conservative for natural chat.
    return max(0.82, min(1.18, 1.0 + pct / 100.0))


def _get_f5_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _MODEL_LOCK:
        if _MODEL is not None:
            return _MODEL
        try:
            from f5_tts.api import F5TTS
        except ImportError as e:
            raise HTTPException(
                status_code=503,
                detail="未安装 F5-TTS。请在单独 Python 环境执行：pip install f5-tts",
            ) from e
        _MODEL = F5TTS(
            model=os.environ.get("F5_TTS_MODEL", "F5TTS_v1_Base"),
            ckpt_file=_env_path("F5_TTS_CKPT_FILE"),
            vocab_file=_env_path("F5_TTS_VOCAB_FILE"),
            device=os.environ.get("F5_TTS_DEVICE", "").strip() or None,
            hf_cache_dir=_env_path("HF_HOME") or None,
        )
        return _MODEL


def _natural_gen_text(body: F5TTSRequest) -> str:
    text = (body.text or body.input or "").strip()
    text = re.sub(r"\s+", " ", text)
    if not text:
        raise HTTPException(status_code=400, detail="text is empty")
    limit = int(os.environ.get("F5_TTS_MAX_CHARS", "450") or 450)
    return text[: max(60, min(1200, limit))]


@app.get("/health")
def health() -> dict[str, Any]:
    ref_audio = _env_path("F5_TTS_REF_AUDIO")
    return {
        "ok": True,
        "engine": "f5-tts",
        "model_loaded": _MODEL is not None,
        "ref_audio_configured": bool(ref_audio),
        "ref_audio_exists": Path(ref_audio).is_file() if ref_audio else False,
    }


@app.post("/tts")
def tts(body: F5TTSRequest):
    text = _natural_gen_text(body)
    ref_audio = _resolve_ref_audio(body)
    model = _get_f5_model()
    speed = float(os.environ.get("F5_TTS_SPEED", "") or _rate_to_speed(body.rate))
    nfe_step = int(os.environ.get("F5_TTS_NFE_STEP", "24") or 24)
    remove_silence = os.environ.get("F5_TTS_REMOVE_SILENCE", "1").strip() != "0"
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = Path(tmp.name)
    try:
        model.infer(
            ref_file=str(ref_audio),
            ref_text=_ref_text(body),
            gen_text=text,
            speed=max(0.75, min(1.25, speed)),
            nfe_step=max(8, min(64, nfe_step)),
            remove_silence=remove_silence,
            file_wave=str(out_path),
            seed=body.seed,
            show_info=lambda *_args, **_kwargs: None,
        )
        audio = out_path.read_bytes()
    finally:
        try:
            out_path.unlink(missing_ok=True)
        except OSError:
            pass
    if not audio:
        raise HTTPException(status_code=500, detail="F5-TTS did not return audio")
    return StreamingResponse(io.BytesIO(audio), media_type="audio/wav")
