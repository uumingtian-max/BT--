"""按名称/扩展名在允许目录内搜索文件（非全盘暴力扫描）。"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from tools.file_ops import KNOWN_BASES, resolve_user_path

MAX_RESULTS = int(os.environ.get("AGENT_SEARCH_FILES_MAX", "80"))
MAX_DEPTH = int(os.environ.get("AGENT_SEARCH_FILES_MAX_DEPTH", "6"))
MAX_SCAN_DIRS = int(os.environ.get("AGENT_SEARCH_FILES_MAX_DIRS", "8000"))


def _match_name(path: Path, query: str, use_regex: bool) -> bool:
    name = path.name
    if use_regex:
        try:
            return bool(re.search(query, name, re.IGNORECASE))
        except re.error:
            return query.lower() in name.lower()
    return query.lower() in name.lower()


def search_files(params: dict[str, Any]) -> str:
    """
    在指定目录下搜索文件。

    params:
        query: 文件名关键字或正则
        directory: 起始目录（desktop/documents/downloads/project 或路径）
        extension: 可选，如 .py .md
        max_results: 默认 50
        regex: 是否把 query 当正则
        modified_within_hours: 仅最近 N 小时内修改
    """
    query = str(params.get("query") or params.get("name") or "").strip()
    if not query and not params.get("extension"):
        return json.dumps({"ok": False, "error": "missing query or extension"}, ensure_ascii=False)

    root_raw = params.get("directory") or params.get("path") or "desktop"
    try:
        root = resolve_user_path(str(root_raw))
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    if not root.exists():
        return json.dumps({"ok": False, "error": f"directory not found: {root}"}, ensure_ascii=False)

    ext = str(params.get("extension") or "").strip()
    if ext and not ext.startswith("."):
        ext = "." + ext
    max_results = max(1, min(MAX_RESULTS, int(params.get("max_results", 50) or 50)))
    use_regex = bool(params.get("regex"))
    within_h = params.get("modified_within_hours")
    cutoff = None
    if within_h is not None:
        cutoff = time.time() - float(within_h) * 3600

    results: list[dict[str, Any]] = []
    scanned = 0

    def walk(base: Path, depth: int) -> None:
        nonlocal scanned
        if depth > MAX_DEPTH or len(results) >= max_results or scanned >= MAX_SCAN_DIRS:
            return
        try:
            entries = list(base.iterdir())
        except (OSError, PermissionError):
            return
        for entry in entries:
            if len(results) >= max_results or scanned >= MAX_SCAN_DIRS:
                return
            scanned += 1
            if entry.name.startswith(".") and entry.name not in (".env", ".gitignore"):
                continue
            try:
                if entry.is_dir():
                    if entry.name.lower() in (
                        "node_modules",
                        ".git",
                        "__pycache__",
                        ".venv",
                        "vendor",
                    ):
                        continue
                    walk(entry, depth + 1)
                elif entry.is_file():
                    if ext and entry.suffix.lower() != ext.lower():
                        continue
                    if query and not _match_name(entry, query, use_regex):
                        continue
                    if cutoff is not None:
                        if entry.stat().st_mtime < cutoff:
                            continue
                    st = entry.stat()
                    results.append(
                        {
                            "path": str(entry),
                            "name": entry.name,
                            "size_kb": round(st.st_size / 1024, 1),
                            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
                        }
                    )
            except (OSError, PermissionError):
                continue

    walk(root.resolve(), 0)
    results.sort(key=lambda x: x.get("modified", ""), reverse=True)

    return json.dumps(
        {
            "ok": True,
            "root": str(root),
            "query": query,
            "extension": ext or None,
            "scanned_entries": scanned,
            "count": len(results),
            "results": results[:max_results],
            "known_bases": list(KNOWN_BASES.keys()),
        },
        ensure_ascii=False,
        indent=2,
    )
