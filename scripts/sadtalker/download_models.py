#!/usr/bin/env python3
"""Download SadTalker checkpoints into ./SadTalker (tracked copy; SadTalker/ is gitignored)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先: pip install requests", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent.parent.parent / "SadTalker"
if not ROOT.is_dir():
    print(f"缺少目录: {ROOT}\n请先 clone SadTalker 到项目根目录。", file=sys.stderr)
    raise SystemExit(1)

os.chdir(ROOT)
(ROOT / "checkpoints").mkdir(exist_ok=True)
(ROOT / "gfpgan" / "weights").mkdir(parents=True, exist_ok=True)

MODELS: dict[str, list[str]] = {
    "checkpoints/mapping_00109-model.pth.tar": [
        "https://hf-mirror.com/vinthony/SadTalker/resolve/main/mapping_00109-model.pth.tar",
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar",
    ],
    "checkpoints/mapping_00229-model.pth.tar": [
        "https://hf-mirror.com/vinthony/SadTalker/resolve/main/mapping_00229-model.pth.tar",
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar",
    ],
    "checkpoints/SadTalker_V0.0.2_256.safetensors": [
        "https://hf-mirror.com/vinthony/SadTalker/resolve/main/SadTalker_V0.0.2_256.safetensors",
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors",
    ],
    "checkpoints/SadTalker_V0.0.2_512.safetensors": [
        "https://hf-mirror.com/vinthony/SadTalker/resolve/main/SadTalker_V0.0.2_512.safetensors",
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors",
    ],
    "gfpgan/weights/GFPGANv1.4.pth": [
        "https://hf-mirror.com/vinthony/SadTalker/resolve/main/GFPGANv1.4.pth",
        "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
    ],
    "gfpgan/weights/alignment_WFLW_4HG.pth": [
        "https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth",
    ],
    "gfpgan/weights/detection_Resnet50_Final.pth": [
        "https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth",
    ],
    "gfpgan/weights/parsing_parsenet.pth": [
        "https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth",
    ],
}


def download_one(dest: Path, urls: list[str]) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    headers: dict[str, str] = {}
    mode = "wb"
    downloaded = 0
    if tmp.exists():
        downloaded = tmp.stat().st_size
        headers["Range"] = f"bytes={downloaded}-"
        mode = "ab"

    last_err: Exception | None = None
    for url in urls:
        try:
            with requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=(30, 600),
                allow_redirects=True,
            ) as resp:
                if resp.status_code == 416:
                    tmp.rename(dest)
                    return
                resp.raise_for_status()
                if resp.status_code == 200 and downloaded and mode == "ab":
                    tmp.unlink(missing_ok=True)
                    downloaded = 0
                    mode = "wb"
                total = resp.headers.get("content-length")
                total_i = (
                    int(total) + downloaded
                    if total and mode == "ab"
                    else int(total)
                    if total
                    else None
                )
                with open(tmp, mode) as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_i:
                            pct = min(100, downloaded * 100 // total_i)
                            print(f"\r  {pct:3d}% ({downloaded // (1024 * 1024)}MB)", end="", flush=True)
            print()
            tmp.rename(dest)
            return
        except Exception as exc:
            last_err = exc
            print(f"\n  失败 {url}: {exc}")
            headers.pop("Range", None)
            if not (tmp.exists() and mode == "ab"):
                tmp.unlink(missing_ok=True)
                downloaded = 0
                mode = "wb"
    raise RuntimeError(f"所有源均失败: {dest}") from last_err


def main() -> int:
    print(f"目标目录: {ROOT}")
    for rel, urls in MODELS.items():
        dest = ROOT / rel
        if dest.is_file() and dest.stat().st_size > 1024:
            print(f"已存在跳过: {rel} ({dest.stat().st_size // (1024 * 1024)}MB)")
            continue
        print(f"下载 {rel} ...")
        download_one(dest, urls)
        print(f"完成: {rel} ({dest.stat().st_size // (1024 * 1024)}MB)")
    print("全部完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
