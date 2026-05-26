"""Edge TTS（支付宝灵光）— 避免 Windows 命令行传中文乱码。"""

from __future__ import annotations

import base64
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

VOICE_ALIASES: dict[str, str] = {
    "alipay_lingguang": "zh-CN-XiaoyiNeural",
    "lingguang": "zh-CN-XiaoyiNeural",
    "灵光": "zh-CN-XiaoyiNeural",
    "支付宝灵光": "zh-CN-XiaoyiNeural",
    "xiaoyi": "zh-CN-XiaoyiNeural",
    "default": "zh-CN-XiaoyiNeural",
}

DEFAULT_VOICE = "zh-CN-XiaoyiNeural"


def resolve_voice(voice: str | None) -> str:
    raw = (voice or "").strip() or DEFAULT_VOICE
    key = raw.lower().replace(" ", "_")
    return VOICE_ALIASES.get(key, raw)


def normalize_request_text(text: str = "", text_b64: str = "") -> str:
    """解析正文；text_b64 为 UTF-8 的 base64（给 PowerShell 等编码不稳的客户端）。"""
    if (text_b64 or "").strip():
        try:
            return base64.b64decode(text_b64.strip()).decode("utf-8").strip()
        except Exception as exc:
            raise ValueError(f"invalid text_b64: {exc}") from exc
    return (text or "").strip()


def _edge_tts_executable() -> str:
    exe = shutil.which("edge-tts")
    if exe:
        return exe
    scripts = Path(sys.executable).resolve().parent / "edge-tts.exe"
    if scripts.is_file():
        return str(scripts)
    return "edge-tts"


def _synthesize_via_cli_file(text: str, voice_id: str) -> tuple[bytes, str | None]:
    """用 --file 传 UTF-8 文本，避免 Windows argv 中文损坏。"""
    exe = _edge_tts_executable()
    txt_path: str | None = None
    mp3_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".txt",
            delete=False,
        ) as tf:
            tf.write(text)
            txt_path = tf.name

        fd, mp3_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        result = subprocess.run(
            [exe, "--voice", voice_id, "--file", txt_path, "--write-media", mp3_path],
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "edge-tts cli failed").strip()
            return b"", err
        data = Path(mp3_path).read_bytes()
        if not data:
            return b"", "edge-tts produced empty mp3"
        return data, None
    except FileNotFoundError:
        return b"", f"edge-tts not found: {exe}"
    except subprocess.TimeoutExpired:
        return b"", "edge-tts timed out"
    except Exception as exc:
        return b"", str(exc)
    finally:
        for p in (txt_path, mp3_path):
            if p and os.path.isfile(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass


async def synthesize_mp3_async(text: str, voice: str | None = None) -> tuple[bytes, str | None]:
    """在 FastAPI 事件循环内直接调用 edge_tts API（推荐）。"""
    cleaned = (text or "").strip()
    if not cleaned:
        return b"", "text is empty"
    voice_id = resolve_voice(voice)
    mp3_path: str | None = None
    try:
        import edge_tts  # type: ignore

        fd, mp3_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        await edge_tts.Communicate(cleaned, voice_id).save(mp3_path)
        data = Path(mp3_path).read_bytes()
        if data:
            return data, None
    except Exception as api_exc:
        log.warning("edge_tts API failed (%r), fallback CLI --file: %s", cleaned[:40], api_exc)
    finally:
        if mp3_path and os.path.isfile(mp3_path):
            try:
                os.unlink(mp3_path)
            except OSError:
                pass

    return _synthesize_via_cli_file(cleaned, voice_id)


def health_status() -> dict[str, Any]:
    exe = _edge_tts_executable()
    api_ok = False
    api_err = ""
    try:
        import edge_tts  # type: ignore

        api_ok = True
        _ = edge_tts
    except Exception as exc:
        api_err = str(exc)
    return {
        "ok": api_ok or bool(exe),
        "engine": "edge-tts",
        "default_voice": DEFAULT_VOICE,
        "aliases": list(VOICE_ALIASES.keys()),
        "cli_path": exe,
        "python_api": api_ok,
        "python_api_error": api_err or None,
        "note": "Windows 请用 --file 或 JSON UTF-8；PowerShell 可用 text_b64",
    }
