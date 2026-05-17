from __future__ import annotations

import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets" / "branding"
PUBLIC = ROOT / "frontend" / "public"
ELECTRON = ROOT / "electron"
SIZES = (16, 24, 32, 48, 64, 96, 128, 192, 256, 512, 1024)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def glow_line(draw: ImageDraw.ImageDraw, pts: list[tuple[int, int]], color: tuple[int, int, int], width: int) -> None:
    for w, a in ((width * 5, 35), (width * 3, 60), (width, 230)):
        draw.line(pts, fill=(*color, a), width=max(1, w), joint="curve")


def draw_icon_mark(img: Image.Image, cx: int, cy: int, size: int) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    core_r = int(size * 0.33)

    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    gd.ellipse(
        (cx - int(size * 0.31), cy - int(size * 0.31), cx + int(size * 0.31), cy + int(size * 0.31)),
        fill=(120, 58, 255, 70),
    )
    gd.ellipse(
        (cx - int(size * 0.23), cy - int(size * 0.23), cx + int(size * 0.23), cy + int(size * 0.23)),
        fill=(14, 10, 34, 130),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=max(8, size // 34)))
    img.alpha_composite(glow)

    for i in range(16):
        a = i * math.tau / 16
        x1 = cx + int(math.cos(a) * core_r * 0.35)
        y1 = cy + int(math.sin(a) * core_r * 0.35)
        x2 = cx + int(math.cos(a) * core_r * 1.15)
        y2 = cy + int(math.sin(a) * core_r * 1.15)
        glow_line(d, [(x1, y1), (x2, y2)], (146, 86, 255), max(3, size // 180))
        dot_r = max(5, size // 70)
        d.ellipse((x2 - dot_r, y2 - dot_r, x2 + dot_r, y2 + dot_r), fill=(94, 234, 212, 210))

    bolt = [
        (cx + int(size * 0.06), cy - int(size * 0.35)),
        (cx - int(size * 0.16), cy - int(size * 0.01)),
        (cx - int(size * 0.01), cy - int(size * 0.01)),
        (cx - int(size * 0.10), cy + int(size * 0.36)),
        (cx + int(size * 0.20), cy - int(size * 0.08)),
        (cx + int(size * 0.05), cy - int(size * 0.08)),
    ]
    d.polygon(bolt, fill=(240, 228, 255, 252))
    d.line(bolt + [bolt[0]], fill=(176, 112, 255, 240), width=max(4, size // 72))


def mark(size: int = 1024, with_text: bool = False, transparent_bg: bool = False) -> Image.Image:
    bg = (0, 0, 0, 0) if transparent_bg else (4, 4, 12, 255)
    img = Image.new("RGBA", (size, size), bg)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = size // 2, int(size * (0.41 if with_text else 0.5))

    if not transparent_bg:
        shell = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shell, "RGBA")
        sd.rounded_rectangle(
            (int(size * 0.11), int(size * 0.11), int(size * 0.89), int(size * 0.89)),
            radius=int(size * 0.18),
            fill=(10, 9, 22, 255),
            outline=(146, 86, 255, 58),
            width=max(2, size // 180),
        )
        shell = shell.filter(ImageFilter.GaussianBlur(radius=max(4, size // 120)))
        img.alpha_composite(shell)
        d = ImageDraw.Draw(img, "RGBA")

    draw_icon_mark(img, cx, cy, size)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=150, threshold=2))

    if with_text:
        d = ImageDraw.Draw(img, "RGBA")
        title = "BLACKLIGHT"
        f1 = font(int(size * 0.07), True)
        y = int(size * 0.77)
        box = d.textbbox((0, 0), title, font=f1)
        x = (size - (box[2] - box[0])) // 2
        d.text((x, y), title, font=f1, fill=(220, 246, 255, 255))
    return img


def resize(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size), Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1, percent=130, threshold=2))


def write_ico(path: Path, master: Image.Image) -> None:
    frames = []
    for s in (256, 128, 64, 48, 32, 24, 16):
        import io
        buf = io.BytesIO()
        resize(master, s).save(buf, "PNG")
        frames.append((s, buf.getvalue()))
    offset = 6 + 16 * len(frames)
    directory = b""
    payload = b""
    for s, data in frames:
        directory += struct.pack("<BBBBHHII", 0 if s >= 256 else s, 0 if s >= 256 else s, 0, 0, 1, 32, len(data), offset)
        payload += data
        offset += len(data)
    path.write_bytes(struct.pack("<HHH", 0, 1, len(frames)) + directory + payload)


def main() -> int:
    BRAND.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    ELECTRON.mkdir(parents=True, exist_ok=True)
    icon = mark(1024, False, True)
    hero = mark(1024, True, False)
    icon.save(BRAND / "blacklight-icon-master.png")
    hero.save(BRAND / "blacklight-hero.png")
    hero.save(BRAND / "onyx-override-hero.png")
    hero.save(BRAND / "hero-square.png")
    hero.save(PUBLIC / "hero.png")
    for s in SIZES:
        resize(icon if s < 128 else hero, s).save(PUBLIC / f"logo-{s}.png")
        resize(icon, s).save(BRAND / f"icon-{s}.png")
        resize(hero, s).save(BRAND / f"brand-full-{s}.png")
    resize(icon, 256).save(PUBLIC / "logo.png")
    resize(hero, 192).save(PUBLIC / "logo192.png")
    resize(hero, 512).save(PUBLIC / "logo512.png")
    for s in (256, 512, 1024):
        resize(icon, s).save(ELECTRON / f"icon-{s}.png")
    resize(icon, 256).save(ELECTRON / "icon.png")
    write_ico(ELECTRON / "icon.ico", icon)
    write_ico(BRAND / "desktop-icon.ico", icon)
    write_ico(PUBLIC / "favicon.ico", icon)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
