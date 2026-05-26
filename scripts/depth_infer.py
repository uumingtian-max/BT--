#!/usr/bin/env python3
"""Depth Anything V2 → photo.png + depth.png for Blacklight digital-human stage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _pick_default_image(project_root: Path) -> Path | None:
    candidates = [
        project_root / "face.png",
        project_root / "photo.png",
        project_root / "assets" / "branding" / "bt-blacklight-hero.png",
        project_root / "assets" / "branding" / "blacklight-hero.png",
        project_root / "frontend" / "public" / "hero.png",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _resolve_device(requested: str) -> str:
    import torch

    req = (requested or "auto").strip().lower()
    if req == "cpu":
        return "cpu"
    if req == "cuda" and torch.cuda.is_available():
        return "cuda"
    if req == "auto":
        if torch.cuda.is_available():
            try:
                cap = torch.cuda.get_device_capability()
                # RTX 5090 (sm_120) may need nightly; try one tiny op
                torch.zeros(1, device="cuda")
                return "cuda"
            except Exception as exc:
                print(f"[depth] CUDA 不可用，回退 CPU: {exc}", file=sys.stderr)
        return "cpu"
    return "cpu"


def run(img_path: Path, out_dir: Path, *, device: str = "auto") -> None:
    import cv2
    import numpy as np
    from PIL import Image
    from transformers import pipeline

    out_dir.mkdir(parents=True, exist_ok=True)
    dev = _resolve_device(device)
    print(f"设备: {dev}")

    print("加载 Depth Anything V2 Small（首次约 100MB）...")
    pipe = pipeline(
        task="depth-estimation",
        model="depth-anything/Depth-Anything-V2-Small-hf",
        device=0 if dev == "cuda" else -1,
    )

    print(f"推理: {img_path}")
    img = Image.open(img_path).convert("RGB")
    result = pipe(img)
    depth = result["depth"]

    depth_arr = np.array(depth, dtype=np.float32)
    depth_norm = cv2.normalize(depth_arr, None, 0, 255, cv2.NORM_MINMAX)
    depth_uint8 = depth_norm.astype(np.uint8)

    photo_out = out_dir / "photo.png"
    depth_out = out_dir / "depth.png"
    img.save(photo_out)
    cv2.imwrite(str(depth_out), depth_uint8)
    print(f"已写入:\n  {photo_out}\n  {depth_out}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="生成黑光 3D 人像深度图")
    parser.add_argument(
        "--image",
        "-i",
        type=Path,
        help="人像照片（默认: face.png 或项目 hero）",
    )
    parser.add_argument(
        "--out-dir",
        "-o",
        type=Path,
        default=root / "frontend" / "public" / "digital-human",
        help="输出目录（默认 frontend/public/digital-human）",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cuda", "cpu"),
        default="auto",
        help="auto=能 CUDA 则用，5090 若 PyTorch 过旧会自动 CPU",
    )
    args = parser.parse_args()

    img = args.image
    if img is None:
        img = _pick_default_image(root)
    if img is None or not img.is_file():
        print(
            "找不到照片。请任选其一：\n"
            f"  1) 复制你的照片为 {root / 'face.png'}\n"
            f"  2) python scripts/depth_infer.py -i 你的照片.jpg\n",
            file=sys.stderr,
        )
        return 1

    try:
        run(img.resolve(), args.out_dir.resolve(), device=args.device)
    except Exception as exc:
        print(f"失败: {exc}", file=sys.stderr)
        if "sm_120" in str(exc) or "CUDA" in str(exc):
            print(
                "\nRTX 5090 请安装 PyTorch nightly 后再试 CUDA，或直接用 CPU：\n"
                "  pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128\n"
                "  python scripts/depth_infer.py --device cpu\n",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
