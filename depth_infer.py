"""兼容入口 → scripts/depth_infer.py"""
from pathlib import Path
import runpy
import sys

if __name__ == "__main__":
    script = Path(__file__).resolve().parent / "scripts" / "digital-human" / "depth_infer.py"
    sys.argv[0] = str(script)
    runpy.run_path(str(script), run_name="__main__")
