import subprocess, sys, os, tempfile

def execute_python(code: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code); tmp = f.name
    try:
        r = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=30)
        out = r.stdout + (("\nSTDERR:\n" + r.stderr) if r.stderr else "")
        return out[:5000] or "(no output)"
    except subprocess.TimeoutExpired: return "Timeout"
    except Exception as e: return f"Error: {e}"
    finally: os.unlink(tmp)
