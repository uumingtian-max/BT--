"""无 SD 时的占位出图（Pillow），避免 generate_image 直接 skipped。"""

from __future__ import annotations

import os
from safe_paths import safe_output_path


def generate_placeholder_image(prompt: str, output_path: str) -> dict:
    from PIL import Image, ImageDraw, ImageFilter

    out = safe_output_path(output_path, default_name="sd_placeholder.png")

    size = 512
    img = Image.new("RGBA", (size, size), (8, 10, 20, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 - 20
    for r, color in [
        (180, (138, 43, 226, 40)),
        (120, (0, 255, 255, 50)),
        (70, (167, 139, 250, 90)),
    ]:
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=(220, 240, 255, 220))
    text = (prompt or "ONYX-OVERRIDE")[:80]
    draw.text((24, size - 72), text, fill=(200, 210, 255, 255))
    draw.text(
        (24, size - 48),
        "placeholder · set ENABLE_LOCAL_SD=1 for SD",
        fill=(120, 130, 160, 255),
    )
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))
    img.save(out, "PNG")
    return {
        "status": "success",
        "image_path": str(out),
        "mode": "placeholder",
        "hint": "未开本地 SD，已生成占位图。开启: ENABLE_LOCAL_SD=1 并安装 requirements-media.txt",
    }


def local_sd_enabled() -> bool:
    return os.environ.get("ENABLE_LOCAL_SD", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def placeholder_enabled() -> bool:
    return os.environ.get("ENABLE_IMAGE_PLACEHOLDER", "1").strip().lower() not in (
        "0",
        "false",
        "off",
        "no",
    )
