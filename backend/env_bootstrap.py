"""Load backend/.env into os.environ before other modules read get_runtime()."""

from __future__ import annotations

import os
import logging
from pathlib import Path


def _parse_log_level(raw: str) -> int:
    name = (raw or "").strip().upper()
    if not name:
        return logging.INFO
    if name.isdigit():
        try:
            return int(name)
        except ValueError:
            return logging.INFO
    level = getattr(logging, name, None)
    return level if isinstance(level, int) else logging.INFO


def configure_root_logging() -> None:
    raw = (os.environ.get("LOG_LEVEL") or os.environ.get("LOGLEVEL") or "").strip()
    level = _parse_log_level(raw) if raw else logging.INFO
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format=fmt, datefmt=datefmt)
    else:
        root.setLevel(level)
        for handler in root.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.formatter is None:
                handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).setLevel(level)


DEFAULT_BACKEND_PORT = 8000

# 这些键以 backend/.env 为准（避免 PowerShell 用户环境里残留的 OLLAMA_NUM_CTX=8192 等覆盖项目配置）
_DOTENV_OVERWRITE_KEYS = frozenset(
    {
        "OLLAMA_NUM_CTX",
        "OLLAMA_RESIDENT_MODELS",
        "OLLAMA_ON_DEMAND_MODELS",
        "OLLAMA_RELEASE_ON_DEMAND",
        "OLLAMA_KEEP_ALIVE",
        "OLLAMA_MAX_LOADED_MODELS",
    }
)


def get_backend_listen_port() -> int:
    raw = (os.environ.get("BACKEND_PORT") or "").strip()
    if raw.isdigit():
        return max(1, min(65535, int(raw)))
    return DEFAULT_BACKEND_PORT


def _apply_dotenv_file(path: Path, *, overwrite_keys: frozenset[str] | None = None) -> None:
    if not path.is_file():
        return
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    overwrite = overwrite_keys or frozenset()
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("export "):
            s = s[7:].strip()
        if "=" not in s:
            continue
        key, _, val = s.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key == "BACKEND_PORT":
            v = val.strip().strip("\"'")
            if v.isdigit():
                os.environ[key] = v
            continue
        if key in _DOTENV_OVERWRITE_KEYS or key in overwrite:
            os.environ[key] = val
        else:
            os.environ.setdefault(key, val)


def load_user_secrets_dotenv() -> None:
    """%USERPROFILE%\\.bt\\secrets.env — 仅填补未设置的密钥（不覆盖 backend/.env 已有值）。"""
    path = Path.home() / ".bt" / "secrets.env"
    _apply_dotenv_file(path)


def load_backend_dotenv() -> None:
    path = Path(__file__).resolve().parent / ".env"
    _apply_dotenv_file(path)


def apply_runtime_defaults() -> None:
    """启动时注入执行内核 + 十一专家默认（可被 backend/.env 覆盖）。"""
    try:
        from execution_kernel import apply_execution_kernel_defaults

        apply_execution_kernel_defaults()
    except Exception:
        try:
            from expert_roles import apply_super_agent_defaults

            apply_super_agent_defaults()
        except Exception:
            pass
