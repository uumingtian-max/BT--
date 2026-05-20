"""Safe local shell execution for Agent (PowerShell on Windows, sh elsewhere)."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from tools.file_ops import PROJECT_ROOT, resolve_user_path

TIMEOUT_SEC = int(os.environ.get("AGENT_SHELL_TIMEOUT_SEC", "120"))
OUTPUT_MAX_CHARS = int(os.environ.get("AGENT_SHELL_OUTPUT_MAX_CHARS", "12000"))
MAX_COMMAND_CHARS = int(os.environ.get("AGENT_SHELL_MAX_COMMAND_CHARS", "4000"))

_BLOCKED_PATTERNS = re.compile(
    r"(rm\s+-rf\s+/|format\s+[a-z]:|Remove-Item\s+.*-Recurse.*C:\\|"
    r"del\s+/[sf]\s+[a-z]:|shutdown\s|restart-computer|"
    r"reg\s+delete\s+HKLM|diskpart\s|bcdedit\s|"
    r"Invoke-WebRequest.*-OutFile.*\.exe)",
    re.IGNORECASE,
)


def _resolve_cwd(cwd: str | None) -> Path:
    raw = (cwd or "project").strip().lower()
    if raw in ("project", "repo", "root", "."):
        return PROJECT_ROOT.resolve()
    if raw in ("desktop", "~/desktop"):
        return resolve_user_path("~/Desktop")
    if raw in ("home", "~"):
        return resolve_user_path("~")
    return resolve_user_path(cwd or "project")


def run_shell(command: str, cwd: str | None = "project", shell: str | None = None) -> str:
    """Run one shell command; returns combined stdout/stderr text."""
    cmd = (command or "").strip()
    if not cmd:
        return "Error: empty command"
    if len(cmd) > MAX_COMMAND_CHARS:
        return f"Error: command too long ({len(cmd)} > {MAX_COMMAND_CHARS})"
    if _BLOCKED_PATTERNS.search(cmd):
        return "Error: command blocked by safety policy (destructive/system-wide ops)"

    workdir = _resolve_cwd(cwd)
    workdir.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }

    if sys.platform == "win32":
        shell_kind = (shell or os.environ.get("AGENT_SHELL", "powershell")).strip().lower()
        if shell_kind in ("cmd", "command"):
            proc_args = ["cmd.exe", "/c", cmd]
        else:
            proc_args = [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                cmd,
            ]
    else:
        proc_args = ["/bin/sh", "-lc", cmd]

    try:
        completed = subprocess.run(
            proc_args,
            cwd=str(workdir),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(5, TIMEOUT_SEC),
        )
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {TIMEOUT_SEC}s"
    except Exception as exc:
        return f"Error: {exc}"

    parts: list[str] = [f"cwd={workdir}", f"exit_code={completed.returncode}"]
    if completed.stdout.strip():
        parts.append("STDOUT:\n" + completed.stdout.strip())
    if completed.stderr.strip():
        parts.append("STDERR:\n" + completed.stderr.strip())
    if not completed.stdout.strip() and not completed.stderr.strip():
        parts.append("(no output)")
    out = "\n".join(parts)
    return out[:OUTPUT_MAX_CHARS]
