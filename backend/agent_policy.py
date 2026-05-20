"""Mecha-inspired policy gate: dumb pipeline, policy before side effects.

Runs after registry risk checks. Blocks writes to sensitive paths and
obviously destructive execute_python patterns when enabled (default on).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from tools.file_ops import PROJECT_ROOT, resolve_user_path

_POLICY_ON = ("1", "true", "yes", "on")


def policy_enabled() -> bool:
    return os.environ.get("AGENT_POLICY_ENABLED", "1").strip().lower() in _POLICY_ON


def policy_strict() -> bool:
    return os.environ.get("AGENT_POLICY_STRICT", "0").strip().lower() in _POLICY_ON


def _block_sensitive_writes() -> bool:
    return os.environ.get("AGENT_POLICY_BLOCK_SENSITIVE", "1").strip().lower() in _POLICY_ON


_SENSITIVE_NAME_RE = re.compile(
    r"(^|/|\\)(\.env(\.|$)|credentials\.json|secrets?\.(json|ya?ml)|id_rsa|\.pem$|\.key$|token\.txt)",
    re.IGNORECASE,
)

_DESTRUCTIVE_PY_RE = re.compile(
    r"(os\.remove\s*\(|shutil\.rmtree\s*\(|subprocess\.[^(]*\([^)]*rm\s+-rf|"
    r"format\s+[a-z]:|Remove-Item\s+.*-Recurse|del\s+/[sf])",
    re.IGNORECASE,
)

_SYSTEM_PATH_WRITE_RE = re.compile(
    r"(C:\\Windows|/etc/|/usr/bin|/System/Library)",
    re.IGNORECASE,
)


def _path_from_tool_params(tool_name: str, params: dict[str, Any]) -> Path | None:
    key = {
        "write_file": "path",
        "read_file": "path",
        "open_path": "path",
        "list_files": "directory",
    }.get(tool_name)
    if not key:
        return None
    raw = params.get(key)
    if not raw:
        return None
    try:
        return resolve_user_path(str(raw))
    except Exception:
        return Path(str(raw))


def check_write_path_policy(path: Path) -> str | None:
    """Return human-readable block reason, or None if allowed."""
    if not _block_sensitive_writes():
        return None
    text = str(path).replace("\\", "/")
    if _SENSITIVE_NAME_RE.search(text):
        return f"策略拒绝：禁止写入敏感路径 `{path.name}`（含 .env / 密钥类文件）。请改写到 outputs/ 或让用户手动编辑。"
    if policy_strict():
        try:
            resolved = path.resolve()
            proj = PROJECT_ROOT.resolve()
            if resolved != proj and proj not in resolved.parents:
                # strict: writes only under project root (outputs/workspace still inside)
                allowed = (proj / "outputs").resolve()
                if allowed not in resolved.parents and resolved != allowed:
                    return (
                        f"策略拒绝（严格模式）：`{resolved}` 不在项目目录内。"
                        f"允许根目录：{proj}"
                    )
        except OSError:
            pass
    return None


def check_execute_python_policy(code: str) -> str | None:
    if not code:
        return None
    if _DESTRUCTIVE_PY_RE.search(code):
        return "策略拒绝：检测到可能破坏性操作（删除/格式化/system 路径），请缩小范围或让用户确认后手动执行。"
    if policy_strict() and _SYSTEM_PATH_WRITE_RE.search(code):
        return "策略拒绝（严格模式）：代码涉及系统目录，已拦截。"
    return None


def check_http_request_policy(params: dict[str, Any]) -> str | None:
    url = str(params.get("url") or "").strip()
    if not url:
        return None
    low = url.lower()
    if not (low.startswith("http://") or low.startswith("https://")):
        return f"策略拒绝：http_request 仅允许 http/https，收到 `{url[:80]}`"
    if policy_strict() and any(h in low for h in ("169.254.", "metadata.google")):
        return "策略拒绝（严格模式）：禁止访问链路本地/metadata 类地址。"
    return None


def check_tool_policy(tool_name: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """
    Return block dict {status, message, policy_rule} or None if allowed.
    """
    if not policy_enabled():
        return None
    params = params or {}

    if tool_name == "write_file":
        p = _path_from_tool_params(tool_name, params)
        if p is not None:
            reason = check_write_path_policy(p)
            if reason:
                return {"status": "policy_denied", "tool": tool_name, "policy_rule": "sensitive_write", "message": reason}

    if tool_name == "execute_python":
        reason = check_execute_python_policy(str(params.get("code") or ""))
        if reason:
            return {"status": "policy_denied", "tool": tool_name, "policy_rule": "destructive_code", "message": reason}

    if tool_name == "http_request":
        reason = check_http_request_policy(params)
        if reason:
            return {"status": "policy_denied", "tool": tool_name, "policy_rule": "http_scheme", "message": reason}

    if tool_name == "kill_process":
        pid = params.get("pid")
        if pid is not None and int(pid) <= 4:
            return {
                "status": "policy_denied",
                "tool": tool_name,
                "policy_rule": "protected_pid",
                "message": f"策略拒绝：不能结束系统 PID={pid}。",
            }

    return None
