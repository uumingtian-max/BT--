"""Web search: prefer duckduckgo-search (DDGS), fallback to legacy DuckDuckGo HTTP."""

from __future__ import annotations

import re
from typing import Any

import httpx


def _search_via_ddgs(query: str) -> str | None:
    """Text search via DDG using the maintained `ddgs` package (renamed from duckduckgo-search)."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS  # type: ignore[import-not-found]
        except ImportError:
            return None
    q = (query or "").strip()
    if not q:
        return None
    try:
        with DDGS() as ddgs:
            hits: list[dict[str, Any]] = list(ddgs.text(q, max_results=10))
    except Exception:
        return None
    if not hits:
        return None
    lines: list[str] = []
    for h in hits[:10]:
        title = str(h.get("title") or "").strip()
        body = str(h.get("body") or h.get("snippet") or "").strip()
        url = str(h.get("href") or h.get("url") or "").strip()
        if not title and not body:
            continue
        chunk = f"· {title}\n  {body}"
        if url:
            chunk += f"\n  {url}"
        lines.append(chunk)
    return "\n\n".join(lines) if lines else None


def _legacy_http_search(query: str) -> str:
    with httpx.Client(timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AIAgent/1.0"}) as client:
        resp = client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1"},
        )
        data = resp.json()
        results: list[str] = []
        if data.get("AbstractText"):
            results.append(str(data["AbstractText"]))
        for t in data.get("RelatedTopics", [])[:5]:
            if isinstance(t, dict) and t.get("Text"):
                results.append(str(t["Text"]))
        if results:
            return "\n".join(results)
        resp2 = client.get("https://html.duckduckgo.com/html/", params={"q": query})
        snippets = re.findall(r'class="result__snippet">(.*?)</a>', resp2.text, re.DOTALL)
        clean = [re.sub(r"<[^>]+>", "", s).strip() for s in snippets[:5]]
        return "\n".join(clean) if clean else "No results"


def web_search(query: str) -> str:
    q = (query or "").strip()
    if not q:
        return "Search error: empty query"

    via = _search_via_ddgs(q)
    if via:
        return via

    try:
        legacy = _legacy_http_search(q)
        if legacy and legacy != "No results":
            return legacy
        return (
            legacy
            + "\n\n提示：若经常无结果，请在 backend 目录执行 `pip install ddgs` 后重启后端（已写入 requirements.txt）。"
        )
    except Exception as e:
        return (
            f"Search error: {e}\n"
            "可安装依赖后重试：cd backend && pip install ddgs"
        )
