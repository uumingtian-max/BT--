"""PolicyGuard — whitelist + pattern sandbox before file/terminal/code tools."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from tools.file_ops import PROJECT_ROOT, WORKSPACE


class SecurityException(PermissionError):
    """Blocked by local execution policy."""


def policy_enabled() -> bool:
    return os.environ.get("AGENT_POLICY_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")


def policy_strict() -> bool:
    return os.environ.get("AGENT_POLICY_STRICT", "0").strip().lower() in ("1", "true", "yes", "on")


def block_sensitive_writes() -> bool:
    return os.environ.get("AGENT_POLICY_BLOCK_SENSITIVE", "1").strip().lower() in ("1", "true", "yes", "on")


class PolicyGuard:
    """Intercept dangerous shell/file patterns before tool handlers run."""

    def __init__(self) -> None:
        self.forbidden_patterns: list[re.Pattern[str]] = [
            re.compile(p, re.IGNORECASE)
            for p in (
                r"rm\s+-rf\s+/",
                r"rm\s+-rf\s+\\",
                r"chmod\s+-R\s+777",
                r"curl\s+[^\n|]*\|\s*(ba)?sh",
                r"wget\s+[^\n|]*\|\s*(ba)?sh",
                r"invoke-webrequest[^\n|]*\|\s*iex",
                r"powershell\s+-enc(odedcommand)?",
                r"format\s+[a-z]:",
                r"mkfs\.",
                r"dd\s+if=",
                r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",
                r"reg\s+delete",
                r"del\s+/[fq]",
            )
        ]
        self.safe_paths: list[Path] = self._load_safe_paths()
        self.sensitive_path_patterns: list[re.Pattern[str]] = [
            re.compile(p, re.IGNORECASE)
            for p in (
                r"\.env$",
                r"\.env\.",
                r"credentials",
                r"secrets?\.(json|ya?ml|toml)$",
                r"id_rsa",
                r"\.pem$",
                r"wallet\.dat",
            )
        ]

    def _load_safe_paths(self) -> list[Path]:
        raw = os.environ.get("AGENT_POLICY_SAFE_PATHS", "").strip()
        paths: list[Path] = []
        if raw:
            for part in raw.split(";"):
                p = part.strip()
                if p:
                    try:
                        paths.append(Path(p).expanduser().resolve())
                    except OSError:
                        continue
        if not paths:
            home = Path.home()
            defaults = [
                PROJECT_ROOT,
                WORKSPACE,
                home / "Desktop",
                home / "Documents",
                home / "Downloads",
                Path(__file__).resolve().parent / "outputs",
            ]
            for p in defaults:
                try:
                    paths.append(p.resolve())
                except OSError:
                    continue
        return paths

    def validate_command(self, cmd: str, path: str | None = None) -> bool:
        text = (cmd or "").strip()
        if not text:
            return True
        for pattern in self.forbidden_patterns:
            if pattern.search(text):
                raise SecurityException(f"Forbidden command pattern: {text[:200]}")
        if path:
            self.validate_path(path)
        return True

    def validate_path(self, path: str, *, action: str = "access") -> bool:
        raw = (path or "").strip()
        if not raw:
            return True
        try:
            resolved = Path(raw).expanduser()
            if not resolved.is_absolute():
                resolved = (PROJECT_ROOT / resolved).resolve()
            else:
                resolved = resolved.resolve()
        except OSError as exc:
            raise SecurityException(f"Invalid path: {raw}") from exc

        if block_sensitive_writes() and action in ("write", "delete"):
            rel = str(resolved).replace("\\", "/")
            for pat in self.sensitive_path_patterns:
                if pat.search(rel):
                    raise SecurityException(f"Sensitive path blocked ({action}): {resolved}")

        if policy_strict():
            if not any(self._is_under(resolved, base) for base in self.safe_paths):
                raise SecurityException(f"Access denied outside safe roots: {resolved}")
        return True

    @staticmethod
    def _is_under(path: Path, base: Path) -> bool:
        try:
            path.relative_to(base)
            return True
        except ValueError:
            return False

    def validate_tool_call(self, tool_name: str, params: dict[str, Any] | None) -> bool:
        if not policy_enabled():
            return True
        p = params or {}
        name = (tool_name or "").strip()

        path_keys = ("path", "directory", "file", "target_path", "output_path")
        for key in path_keys:
            val = p.get(key)
            if isinstance(val, str) and val.strip():
                action = "write" if name in ("write_file",) else "access"
                self.validate_path(val, action=action)

        if name == "execute_python":
            code = str(p.get("code") or "")
            self.validate_command(code)
            if policy_strict():
                for bad in ("os.system", "subprocess.call", "subprocess.run", "__import__('os')"):
                    if bad in code.replace(" ", ""):
                        raise SecurityException(f"Blocked construct in execute_python: {bad}")

        if name == "http_request":
            url = str(p.get("url") or "")
            if url.lower().startswith(("file://", "gopher://", "ftp://")):
                raise SecurityException(f"Blocked URL scheme: {url[:120]}")

        if name in ("browser_navigate", "open_url"):
            url = str(p.get("url") or "")
            if url and not url.startswith(("http://", "https://")):
                raise SecurityException("Only http/https URLs allowed")

        return True


_GUARD: PolicyGuard | None = None


def get_policy_guard() -> PolicyGuard:
    global _GUARD
    if _GUARD is None:
        _GUARD = PolicyGuard()
    return _GUARD


def check_policy(tool_name: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Return policy_denied block dict or None if allowed."""
    try:
        get_policy_guard().validate_tool_call(tool_name, params)
        return None
    except SecurityException as exc:
        return {
            "status": "policy_denied",
            "policy_rule": "PolicyGuard",
            "tool": tool_name,
            "message": str(exc),
        }
