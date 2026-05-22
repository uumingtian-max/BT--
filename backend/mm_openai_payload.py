"""BT 上传附件 → OpenAI 多模态 messages（vLLM Nemotron Omni）。仅结构化 attachments，不再解析 prompt 路径。"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import httpx

_LEGACY_ATTACHMENT_BLOCK = re.compile(r"\n*\[上传附件\][\s\S]*", re.IGNORECASE)

_BACKEND_ROOT = Path(__file__).resolve().parent

_IMAGE_CT = ("image/",)
_VIDEO_CT = ("video/",)
_AUDIO_CT = ("audio/",)


def omni_mm_enabled() -> bool:
    return os.environ.get("AGENT_OMNI_MM_ENABLED", "1").strip().lower() not in (
        "0",
        "false",
        "off",
        "no",
    )


def strip_legacy_attachment_prompt(text: str) -> str:
    """去掉历史消息里「路径进 prompt」旧格式，避免模型仅凭路径瞎猜。"""
    return _LEGACY_ATTACHMENT_BLOCK.sub("", text or "").strip()


def normalize_attachments(raw: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if not path:
            continue
        out.append(
            {
                "path": path,
                "filename": str(item.get("filename") or "").strip(),
                "content_type": str(item.get("content_type") or "").strip(),
            }
        )
    return out


def win_path_to_vllm_file_url(path: str) -> str:
    """Windows 路径 → vLLM WSL 可读的 file:// URL。"""
    p = Path(path.strip().strip('"').strip("'"))
    if not p.is_absolute():
        p = (_BACKEND_ROOT / p).resolve()
    else:
        p = p.resolve()
    if not p.is_file():
        raise FileNotFoundError(str(p))
    s = p.as_posix()
    if len(s) >= 2 and s[1] == ":":
        drive = s[0].lower()
        rest = s[2:].lstrip("/\\")
        return f"file:///mnt/{drive}/{rest}"
    return f"file://{s}"


def _part_for_attachment(att: dict[str, str]) -> dict[str, Any] | None:
    ctype = (att.get("content_type") or "").lower()
    try:
        url = win_path_to_vllm_file_url(att.get("path") or "")
    except OSError:
        return None
    if any(ctype.startswith(p) for p in _IMAGE_CT):
        return {"type": "image_url", "image_url": {"url": url}}
    if any(ctype.startswith(p) for p in _VIDEO_CT):
        return {"type": "video_url", "video_url": {"url": url}}
    if any(ctype.startswith(p) for p in _AUDIO_CT):
        return {"type": "input_audio", "input_audio": {"data": url, "format": "wav"}}
    return None


def build_user_content(
    message: str,
    attachments: list[dict[str, str]] | None = None,
) -> str | list[dict[str, Any]]:
    text = strip_legacy_attachment_prompt(message) or "请分析我上传的附件。"
    atts = normalize_attachments(attachments)  # type: ignore[arg-type]
    if not omni_mm_enabled() or not atts:
        return text
    parts: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for att in atts:
        part = _part_for_attachment(att)
        if part:
            parts.append(part)
    media = [p for p in parts if p.get("type") != "text"]
    if not media:
        return text
    return parts


def apply_multimodal_to_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """对带 attachments 的 user 消息注入多模态 content。"""
    if not omni_mm_enabled() or not messages:
        return messages
    out: list[dict[str, Any]] = []
    for m in messages:
        row = dict(m)
        if row.get("role") == "user":
            atts = normalize_attachments(row.pop("attachments", None))  # type: ignore[arg-type]
            raw = row.get("content", "")
            if isinstance(raw, str):
                raw = strip_legacy_attachment_prompt(raw)
                row["content"] = build_user_content(raw, atts) if atts else raw
        out.append(row)
    return out


def attachment_requires_vllm(attachments: list[dict[str, Any]] | None) -> bool:
    return bool(normalize_attachments(attachments))  # type: ignore[arg-type]


def check_vllm_gateway_ready() -> tuple[bool, str]:
    """同步探测 OpenAI 兼容网关 /health（vLLM 常在 /health 而非 /v1/health）。"""
    from agent_runtime import get_runtime

    rt = get_runtime()
    if rt.llm_backend != "openai_compatible":
        return False, "LLM_BACKEND 不是 openai_compatible，无法多模态理解附件"
    base = (rt.openai_base_url or "").strip().rstrip("/")
    if not base:
        return False, "未配置 OPENAI_BASE_URL"
    root = base
    if root.endswith("/v1"):
        root = root[:-3]
    url = f"{root}/health"
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.get(url)
            if r.status_code == 200:
                return True, ""
            return False, f"网关 health HTTP {r.status_code}"
    except Exception as e:
        return False, f"网关不可达: {type(e).__name__}: {e}"


def assert_attachments_can_run(attachments: list[dict[str, Any]] | None) -> None:
    """有附件时必须 vLLM 就绪，否则直接失败（禁止路径进 prompt 让模型猜）。"""
    if not attachment_requires_vllm(attachments):
        return
    if not omni_mm_enabled():
        raise RuntimeError("已禁用 AGENT_OMNI_MM_ENABLED，无法分析附件")
    ok, detail = check_vllm_gateway_ready()
    if not ok:
        raise RuntimeError(
            detail
            or "vLLM Nemotron 未就绪。请先运行 scripts/start-omni-vllm-wsl.sh，确认 :8001/health 为 200。"
        )
