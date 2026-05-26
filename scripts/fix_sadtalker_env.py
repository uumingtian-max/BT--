#!/usr/bin/env python3
"""One-shot fixes for conda env sadtalker (basicsr + pkg_resources/librosa)."""

from __future__ import annotations

import subprocess
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")


def ensure_pkg_resources() -> bool:
    try:
        import pkg_resources  # noqa: F401

        return True
    except ModuleNotFoundError:
        pass
    print("安装 setuptools<70（恢复 pkg_resources，供 librosa 使用）...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "setuptools==69.5.1", "--no-cache-dir", "-q"]
    )
    import pkg_resources  # noqa: F401

    print("pkg_resources OK")
    return True


def main() -> int:
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    patch = subprocess.run(
        [sys.executable, str(root / "scripts" / "patch_sadtalker_basicsr.py")],
        check=False,
    )
    if patch.returncode != 0:
        return patch.returncode
    try:
        ensure_pkg_resources()
        import librosa  # noqa: F401

        print("librosa import OK")
    except Exception as exc:
        print(f"librosa 仍失败: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
