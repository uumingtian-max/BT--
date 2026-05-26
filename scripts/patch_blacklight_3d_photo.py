#!/usr/bin/env python3
"""把 blacklight_3d_final.html 内嵌 base64 改为加载 digital-human/photo.png（便于换脸）。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "frontend" / "public" / "blacklight_3d_final.html"
REPLACEMENT = "const PHOTO_SRC = './digital-human/photo.png'"


def main() -> int:
    if not HTML.is_file():
        print(f"缺少 {HTML}", file=sys.stderr)
        return 1
    text = HTML.read_text(encoding="utf-8", errors="replace")
    if REPLACEMENT in text:
        print("已是外部 photo 路径，跳过")
        return 0
    new_text, n = re.subn(
        r"const PHOTO_SRC = 'data:image/[^']+'",
        REPLACEMENT,
        text,
        count=1,
    )
    if n != 1:
        print("未找到 PHOTO_SRC base64，未修改", file=sys.stderr)
        return 1
    HTML.write_text(new_text, encoding="utf-8")
    print(f"已更新 {HTML} → 使用 ./digital-human/photo.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
