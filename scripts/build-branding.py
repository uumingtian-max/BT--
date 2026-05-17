"""ONYX-OVERRIDE — 全平台高清图标（多尺寸 PNG-in-ICO + 按显示尺寸导出）。"""
from __future__ import annotations

import io
import struct
import sys
from pathlib import Path

try:
    from PIL import Image, ImageFilter, ImageOps
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "-q"])
    from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets" / "branding"
HERO = BRAND / "onyx-override-hero.png"
PUBLIC = ROOT / "frontend" / "public"
ELECTRON = ROOT / "electron"

CURSOR_HQ = Path(
    r"C:\Users\ROG\.cursor\projects\c-Users-ROG-Desktop-ai-agent-project\assets"
    r"\c__Users_ROG_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images"
    r"_image-4e3159b1-f3fc-475c-89ad-cdfcc70f33ef-0339d9f1-d322-43f8-8b59-825be1fb1e80.png"
)

ICO_SIZES = (256, 128, 64, 48, 32, 24, 16)
UI_LOGO_SIZES = (16, 24, 32, 48, 64, 96, 128, 192, 256, 512, 1024)
BG_RGBA = (10, 10, 15, 255)  # --bg #0a0a0f，与界面一致
MARK_SCALE = 0.72  # 小图标留白，细节在 16–48px 仍可辨认


def resolve_hero_path() -> Path:
    if CURSOR_HQ.is_file():
        return CURSOR_HQ
    return HERO


def extract_brain(img: Image.Image) -> Image.Image:
    """小图标专用：只保留上半部大脑，绝不包含底部 ONYX-OVERRIDE 文字。"""
    w, h = img.size
    top = int(h * 0.03)
    bottom = int(h * 0.56)  # 文字在更下方，此处截断
    band_h = bottom - top
    side = min(w, band_h)
    left = (w - side) // 2
    return img.crop((left, top, left + side, top + side))


def square_hero(img: Image.Image) -> Image.Image:
    w, h = img.size
    side = min(w, h)
    return img.crop(((w - side) // 2, 0, (w + side) // 2, side))


def sharpen(img: Image.Image, *, strong: bool = False) -> Image.Image:
    return img.filter(
        ImageFilter.UnsharpMask(
            radius=1.8 if strong else 1.0,
            percent=220 if strong else 150,
            threshold=2,
        )
    )


def to_master(subject: Image.Image, px: int = 1024) -> Image.Image:
    subject = subject.convert("RGBA")
    if subject.size != (px, px):
        subject = ImageOps.fit(
            subject, (px, px), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)
        )
    return sharpen(subject)


def compose_on_bg(subject: Image.Image, px: int, *, scale: float = MARK_SCALE) -> Image.Image:
    """品牌脑图标：深色底 + 居中缩放，避免小尺寸糊成一团。"""
    subject = subject.convert("RGBA")
    canvas = Image.new("RGBA", (px, px), BG_RGBA)
    side = max(1, int(px * scale))
    fitted = ImageOps.fit(
        subject, (side, side), method=Image.Resampling.LANCZOS, centering=(0.5, 0.48)
    )
    ox = (px - side) // 2
    oy = (px - side) // 2
    canvas.paste(fitted, (ox, oy), fitted)
    return canvas


def compose_full_brand(hero: Image.Image, px: int) -> Image.Image:
    """完整品牌（脑 + ONYX-OVERRIDE 字样），用于侧栏/空状态等较大展示。"""
    hero = hero.convert("RGBA")
    if hero.size != (px, px):
        hero = ImageOps.fit(hero, (px, px), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    return sharpen(hero)


def downscale(master: Image.Image, size: int) -> Image.Image:
    if master.width == size:
        return sharpen(master.copy(), strong=size <= 48)
    # 两步缩小，减轻 16–64px 的锯齿与发糊
    cur = master
    while cur.width > size * 2 and cur.width > 64:
        nxt = max(size * 2, 64)
        cur = cur.resize((nxt, nxt), Image.Resampling.LANCZOS)
    out = cur.resize((size, size), Image.Resampling.LANCZOS)
    return sharpen(out, strong=size <= 48)


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=3)
    return buf.getvalue()


def write_ico_png(path: Path, master: Image.Image, sizes: tuple[int, ...] = ICO_SIZES) -> int:
    """Windows Vista+：ICO 内嵌多帧 PNG，桌面/任务栏各 DPI 都清晰。"""
    entries: list[tuple[int, bytes]] = []
    for size in sorted(sizes, reverse=True):
        entries.append((size, png_bytes(downscale(master, size))))

    count = len(entries)
    header = struct.pack("<HHH", 0, 1, count)
    dir_size = 6 + 16 * count
    offset = dir_size
    directory = b""
    payload = b""
    for size, data in entries:
        w = h = size
        directory += struct.pack(
            "<BBBBHHII",
            0 if w >= 256 else w,
            0 if h >= 256 else h,
            0,
            0,
            1,
            32,
            len(data),
            offset,
        )
        payload += data
        offset += len(data)
    path.write_bytes(header + directory + payload)
    return count


def ico_embedded_count(path: Path) -> int:
    if path.stat().st_size < 6:
        return 0
    return struct.unpack("<H", path.read_bytes()[4:6])[0]


def export_png_set(master: Image.Image, dest_dir: Path, prefix: str, sizes: tuple[int, ...]) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for size in sizes:
        out = dest_dir / f"{prefix}-{size}.png"
        downscale(master, size).save(out, "PNG", optimize=False)


def main() -> int:
    hero_path = resolve_hero_path()
    if not hero_path.is_file():
        print(f"Missing hero: {hero_path}")
        return 1

    BRAND.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    ELECTRON.mkdir(parents=True, exist_ok=True)

    src = Image.open(hero_path).convert("RGBA")
    src.save(HERO, "PNG")

    brain = extract_brain(src)
    hero_sq = square_hero(src)
    mark_master = compose_on_bg(to_master(brain, 1024), 1024)
    full_master = compose_full_brand(hero_sq, 1024)

    mark_master.save(BRAND / "icon-master-1024.png", "PNG")
    full_master.save(BRAND / "brand-full-1024.png", "PNG")
    brain.save(BRAND / "icon-subject.png", "PNG")

    export_png_set(mark_master, BRAND, "icon", UI_LOGO_SIZES)
    export_png_set(full_master, BRAND, "brand-full", UI_LOGO_SIZES)
    export_png_set(mark_master, ELECTRON, "icon", (128, 256, 512, 1024))

    # UI：小图用脑标，≥128 用完整品牌图
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for size in UI_LOGO_SIZES:
        src_master = full_master if size >= 128 else mark_master
        downscale(src_master, size).save(PUBLIC / f"logo-{size}.png", "PNG", optimize=False)

    hero_sq.save(PUBLIC / "hero.png", "PNG", optimize=False)
    hero_sq.save(BRAND / "hero-square.png", "PNG", optimize=False)

    downscale(mark_master, 256).save(BRAND / "app-icon.png", "PNG", optimize=False)
    downscale(mark_master, 256).save(PUBLIC / "logo.png", "PNG", optimize=False)
    downscale(full_master, 192).save(PUBLIC / "logo192.png", "PNG", optimize=False)
    downscale(full_master, 512).save(PUBLIC / "logo512.png", "PNG", optimize=False)
    downscale(full_master, 256).save(ELECTRON / "icon.png", "PNG", optimize=False)

    for ico in (ELECTRON / "icon.ico", BRAND / "desktop-icon.ico", PUBLIC / "favicon.ico"):
        n = write_ico_png(ico, mark_master)
        print(f"  OK  {ico.relative_to(ROOT)}  ({n} PNG frames)")

    print("Branding OK — all surfaces use 1024px master.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
