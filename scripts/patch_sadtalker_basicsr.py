#!/usr/bin/env python3
"""Fix basicsr for torchvision>=0.18 (functional_tensor removed). Run inside conda env sadtalker."""

from __future__ import annotations

import sys
from pathlib import Path

OLD = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
NEW = "from torchvision.transforms.functional import rgb_to_grayscale"


def find_degradations_files() -> list[Path]:
    import site

    roots: list[Path] = []
    for p in site.getsitepackages():
        roots.append(Path(p))
    try:
        import basicsr  # noqa: F401
    except Exception:
        pass
    else:
        import basicsr as bs

        roots.append(Path(bs.__file__).resolve().parent)

    found: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        f = root / "data" / "degradations.py"
        if f.is_file():
            rp = f.resolve()
            if rp not in seen:
                seen.add(rp)
                found.append(rp)
    # Windows conda default layout
    env = Path(sys.prefix)
    for sub in ("Lib/site-packages", "lib/site-packages"):
        f = env / sub / "basicsr" / "data" / "degradations.py"
        if f.is_file():
            rp = f.resolve()
            if rp not in seen:
                seen.add(rp)
                found.append(rp)
    return found


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if NEW in text:
        print(f"already ok: {path}")
        return True
    if OLD not in text:
        print(f"skip (pattern missing): {path}")
        return False
    path.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print(f"patched: {path}")
    return True


def main() -> int:
    files = find_degradations_files()
    if not files:
        print("找不到 basicsr/data/degradations.py，请先: pip install basicsr==1.4.2 --no-cache-dir", file=sys.stderr)
        return 1
    ok = all(patch_file(f) for f in files)
    if ok:
        try:
            import basicsr  # noqa: F401

            print("basicsr import OK")
        except Exception as exc:
            print(f"basicsr import 仍失败: {exc}", file=sys.stderr)
            return 1
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
