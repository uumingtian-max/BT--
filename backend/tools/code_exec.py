from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
WORKSPACE.mkdir(parents=True, exist_ok=True)
MAX_CODE_CHARS = int(os.environ.get("AGENT_PYTHON_MAX_CODE_CHARS", "20000"))
TIMEOUT_SEC = int(os.environ.get("AGENT_PYTHON_TIMEOUT_SEC", "30"))
OUTPUT_MAX_CHARS = int(os.environ.get("AGENT_PYTHON_OUTPUT_MAX_CHARS", "5000"))


def execute_python(code: str) -> str:
    if not isinstance(code, str) or not code.strip():
        return "Error: missing Python code"
    if len(code) > MAX_CODE_CHARS:
        return f"Error: code too large ({len(code)} chars > {MAX_CODE_CHARS})"

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix="agent_exec_",
        dir=str(WORKSPACE),
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(code)
        tmp = f.name
    try:
        env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TEMP": str(WORKSPACE),
            "TMP": str(WORKSPACE),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
        r = subprocess.run(
            [sys.executable, "-I", tmp],
            cwd=str(WORKSPACE),
            env=env,
            capture_output=True,
            text=True,
            timeout=max(1, TIMEOUT_SEC),
        )
        out = r.stdout + (("\nSTDERR:\n" + r.stderr) if r.stderr else "")
        if r.returncode:
            out = f"exit_code={r.returncode}\n{out}"
        return out[:OUTPUT_MAX_CHARS] or "(no output)"
    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {e}"
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
