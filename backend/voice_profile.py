"""单一语音档案：默认灵光，可随习惯/配置升级（generation 递增）。"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from lingguang_tts import DEFAULT_VOICE, resolve_voice

_PROFILE_PATH = Path(__file__).resolve().parent / "data" / "voice_profile.json"

# 进化池：习惯体检通过后可轮换更短的「大佬模式」开场
_STARTUP_POOL: tuple[str, ...] = (
    "黑光已就位，等待指令",
    "黑光在线，直接说任务",
    "已就绪，只说结果",
)

_DEFAULT_PROFILE: dict[str, Any] = {
    "version": 1,
    "generation": 1,
    "voice": "alipay_lingguang",
    "startup_text": _STARTUP_POOL[0],
    "short_ack": "收到",
    "startup_on_boot": True,
    "evolve_enabled": True,
    "history": [],
}


def _env_bool(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() not in ("0", "false", "off", "no")


def load_profile() -> dict[str, Any]:
    env_voice = (os.environ.get("VOICE_ID") or os.environ.get("BKLT_VOICE") or "").strip()
    env_startup = (os.environ.get("VOICE_STARTUP_TEXT") or "").strip()
    if _PROFILE_PATH.is_file():
        try:
            data = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                prof = {**_DEFAULT_PROFILE, **data}
            else:
                prof = dict(_DEFAULT_PROFILE)
        except (OSError, json.JSONDecodeError):
            prof = dict(_DEFAULT_PROFILE)
    else:
        prof = dict(_DEFAULT_PROFILE)
    if env_voice:
        prof["voice"] = env_voice
    if env_startup:
        prof["startup_text"] = env_startup
    prof["voice_resolved"] = resolve_voice(str(prof.get("voice") or DEFAULT_VOICE))
    prof["startup_on_boot"] = _env_bool("VOICE_STARTUP_ON_BOOT", "1" if prof.get("startup_on_boot", True) else "0")
    prof["evolve_enabled"] = _env_bool("VOICE_EVOLVE", "1" if prof.get("evolve_enabled", True) else "0")
    return prof


def save_profile(prof: dict[str, Any]) -> dict[str, Any]:
    _PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean = {k: v for k, v in prof.items() if k != "voice_resolved"}
    _PROFILE_PATH.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    return load_profile()


def apply_patch(patch: dict[str, Any], *, reason: str = "manual") -> dict[str, Any]:
    prof = load_profile()
    changed: list[str] = []
    for key in ("voice", "startup_text", "short_ack", "startup_on_boot"):
        if key in patch and patch[key] is not None and prof.get(key) != patch[key]:
            prof[key] = patch[key]
            changed.append(key)
    if not changed:
        return prof
    prof["generation"] = int(prof.get("generation") or 1) + 1
    prof["version"] = int(prof.get("version") or 1)
    hist = list(prof.get("history") or [])
    hist.append(
        {
            "ts": int(time.time()),
            "generation": prof["generation"],
            "reason": reason,
            "changed": changed,
            "startup_text": prof.get("startup_text"),
            "voice": prof.get("voice"),
        }
    )
    prof["history"] = hist[-24:]
    return save_profile(prof)


def maybe_evolve_from_habit(*, summary: str = "", boss_mode_hint: bool = False) -> dict[str, Any] | None:
    """习惯体检后自动升级开场白（仍是一个语音通道，只改文案/代数）。"""
    prof = load_profile()
    if not prof.get("evolve_enabled"):
        return None
    gen = int(prof.get("generation") or 1)
    if gen >= len(_STARTUP_POOL):
        return None
  # 大佬模式或摘要里提到「只要结果」→ 进化到更短开场
    text_l = (summary or "").lower()
    trigger = boss_mode_hint or any(k in text_l for k in ("只要结果", "大佬", "boss", "别过程"))
    if not trigger:
        return None
    next_text = _STARTUP_POOL[min(gen, len(_STARTUP_POOL) - 1)]
    if prof.get("startup_text") == next_text:
        return None
    return apply_patch({"startup_text": next_text}, reason="habit_evolve")


def public_status() -> dict[str, Any]:
    p = load_profile()
    return {
        "ok": True,
        "generation": p.get("generation"),
        "voice": p.get("voice"),
        "voice_resolved": p.get("voice_resolved"),
        "startup_text": p.get("startup_text"),
        "short_ack": p.get("short_ack"),
        "startup_on_boot": p.get("startup_on_boot"),
        "evolve_enabled": p.get("evolve_enabled"),
        "profile_path": str(_PROFILE_PATH),
        "history_count": len(p.get("history") or []),
    }
