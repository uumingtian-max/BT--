#!/usr/bin/env python3
"""从桌面 blacklight_3d.html 提取内嵌 PHOTO → frontend/public/digital-human/photo.png"""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    candidates = [
        Path(r"C:\Users\ROG\Desktop\blacklight_3d.html"),
        root / "blacklight_3d.html",
    ]
    html_path = next((p for p in candidates if p.is_file()), None)
    if not html_path:
        print("找不到 blacklight_3d.html（请放在桌面或项目根目录）", file=sys.stderr)
        return 1

    text = html_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"const\s+PHOTO\s*=\s*['\"]data:image/[^;]+;base64,([^'\"]+)['\"]", text)
    if not m:
        print("未找到 PHOTO base64", file=sys.stderr)
        return 1

    raw = m.group(1).strip()
    data = base64.b64decode(raw)
    out = root / "frontend" / "public" / "digital-human" / "photo.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"已写入 {out} ({len(data)} bytes)")
    print("下一步: python scripts/depth_infer.py --device cpu")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
