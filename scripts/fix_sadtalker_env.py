"""兼容入口 → scripts/sadtalker/fix_env.py"""
from pathlib import Path
import runpy
import sys

if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "sadtalker" / "fix_env.py"
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
