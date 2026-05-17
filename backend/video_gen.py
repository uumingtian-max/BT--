"""Unified video generation helpers.

The heavy AI backends are optional.  This module keeps the API usable by
supporting deterministic slideshow/prompt-placeholder videos when imageio is
installed, and returning an honest skipped status when the optional stack is not
available.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from safe_paths import safe_output_path


def _resolve_input_image(root: Path, raw: str) -> Path:
    p = Path(str(raw or "").strip().strip('"\''))
    if not p.is_absolute():
        p = root / p
    return p.resolve()


def _load_imageio() -> Any | None:
    try:
        import imageio.v2 as imageio

        return imageio
    except Exception:
        return None


def _render_prompt_frames(prompt: str, frame_count: int = 24) -> list[Any]:
    from PIL import Image, ImageDraw, ImageFilter

    frames = []
    text = (prompt or "ONYX-OVERRIDE video")[:120]
    for i in range(frame_count):
        img = Image.new("RGB", (768, 432), (8, 10, 20))
        draw = ImageDraw.Draw(img)
        offset = int(40 + i * 4)
        for r, color in [(180, (38, 161, 123)), (130, (86, 108, 214)), (80, (220, 160, 72))]:
            draw.ellipse((offset - r, 216 - r, offset + r, 216 + r), fill=color)
        img = img.filter(ImageFilter.GaussianBlur(radius=18))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 320, 768, 432), fill=(5, 7, 13))
        draw.text((32, 344), text, fill=(230, 236, 255))
        draw.text((32, 388), "placeholder video - configure VIDEO_GEN_BACKEND for model generation", fill=(142, 154, 178))
        frames.append(img)
    return frames


def _render_slideshow(root: Path, image_paths: list[str], out: Path, fps: float) -> dict[str, Any]:
    imageio = _load_imageio()
    if imageio is None:
        return {
            "status": "skipped",
            "hint": "缺少 imageio。安装 backend/requirements-media.txt 后可用图片生成视频。",
        }

    from PIL import Image

    frames = []
    missing = []
    for raw in image_paths:
        path = _resolve_input_image(root, raw)
        if not path.is_file():
            missing.append(str(path))
            continue
        img = Image.open(path).convert("RGB")
        img.thumbnail((1280, 720))
        canvas = Image.new("RGB", (1280, 720), (8, 10, 20))
        x = (1280 - img.width) // 2
        y = (720 - img.height) // 2
        canvas.paste(img, (x, y))
        frames.append(canvas)
    if not frames:
        return {"status": "error", "hint": "没有可用图片", "missing": missing[:10]}
    repeated = []
    repeats = max(1, int(max(0.2, fps)))
    for frame in frames:
        repeated.extend([frame] * repeats)
    imageio.mimsave(str(out), repeated, fps=max(1, int(max(1.0, fps))))
    return {
        "status": "success",
        "video_path": str(out),
        "mode": "slideshow",
        "frames": len(repeated),
        "missing": missing[:10],
    }


def _render_prompt_placeholder(prompt: str, out: Path, fps: float) -> dict[str, Any]:
    if os.environ.get("ENABLE_VIDEO_PLACEHOLDER", "1").strip().lower() in ("0", "false", "off", "no"):
        return {
            "status": "skipped",
            "hint": "文生视频需要配置 VIDEO_GEN_BACKEND=wan|cogvideox|auto，或开启 ENABLE_VIDEO_PLACEHOLDER=1。",
        }
    imageio = _load_imageio()
    if imageio is None:
        return {
            "status": "skipped",
            "hint": "缺少 imageio。安装 backend/requirements-media.txt 后可生成占位视频。",
        }
    frames = _render_prompt_frames(prompt)
    imageio.mimsave(str(out), frames, fps=max(1, int(max(1.0, fps))))
    return {
        "status": "success",
        "video_path": str(out),
        "mode": "placeholder",
        "hint": "未接入真实文生视频模型，已生成占位视频。",
    }


def generate_video_unified(
    root: Path,
    outputs_dir: Path,
    *,
    prompt: str,
    image_paths: list[str],
    output_path: str,
    fps: float,
) -> dict[str, Any]:
    del outputs_dir
    try:
        out = safe_output_path(output_path, default_name="agent_video.mp4")
    except ValueError as e:
        return {"status": "error", "hint": str(e)}

    clean_paths = [str(p).strip() for p in image_paths or [] if str(p).strip()]
    if clean_paths:
        return _render_slideshow(root, clean_paths, out, fps)
    if (prompt or "").strip():
        backend = os.environ.get("VIDEO_GEN_BACKEND", "").strip().lower()
        if backend and backend not in {"auto", "wan", "cogvideox"}:
            return {"status": "error", "hint": f"不支持的视频后端：{backend}"}
        return _render_prompt_placeholder(prompt, out, fps or 8)
    return {"status": "error", "hint": "需要 prompt 或 image_paths"}
