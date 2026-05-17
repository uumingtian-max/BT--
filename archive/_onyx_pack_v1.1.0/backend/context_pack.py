"""
Shrink text before it hits the LLM (inspired by OpenHuman TokenJuice ideas):
strip HTML-ish noise, shorten URLs, collapse whitespace, hard cap with head/tail.
Dependency-free.
"""

from __future__ import annotations

import re
from typing import Match


_TAG_RE = re.compile(r"<[^>]{0,500}?>", re.DOTALL)
_URL_RE = re.compile(r"https?://[^\s)\]>\"']{8,500}")
# data:image/png;base64,... 等大段内嵌数据会撑爆上下文
_DATA_URI_RE = re.compile(
    r"data:[^,\s]+,[A-Za-z0-9+/=\s]{80,}",
    re.IGNORECASE,
)
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n{3,}")

_SEARCH_TOOLS = frozenset({"web_search", "local_search"})
_FILE_TOOLS = frozenset({"read_file", "list_files", "write_file"})
_DB_TOOLS = frozenset({"query_database"})


def _short_url(m: Match[str]) -> str:
    u = m.group(0)
    if len(u) <= 48:
        return u
    return u[:32] + "…" + u[-10:]


def _preprocess_for_llm(text: str) -> str:
    if not text:
        return ""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = _TAG_RE.sub(" ", t)
    t = _URL_RE.sub(_short_url, t)
    t = _DATA_URI_RE.sub("[base64 data omitted]", t)
    t = _WS_RE.sub(" ", t)
    return _BLANK_LINES.sub("\n\n", t).strip()


def _hard_truncate(t: str, max_chars: int, note: str) -> str:
    prefix_est = (len(note) + 36) if note else 24
    mid = 4
    body_budget = max_chars - prefix_est - mid - 12
    if body_budget < 120:
        body_budget = max(80, max_chars - 40)
    head = body_budget // 2
    tail = body_budget - head
    if tail < 40:
        tail = 40
        head = max(40, body_budget - tail)
    omitted = max(0, len(t) - head - tail)
    prefix = f"[{note} truncated {omitted} chars]\n" if note else f"[truncated {omitted} chars]\n"
    return prefix + t[:head] + "\n…\n" + t[-tail:]


def compress_for_llm(text: str, max_chars: int, note: str = "") -> str:
    t = _preprocess_for_llm(text)
    if not t:
        return ""
    if len(t) <= max_chars:
        return t
    return _hard_truncate(t, max_chars, note)


def compress_tool_result_for_llm(text: str, max_chars: int, tool_name: str) -> str:
    """按工具类型做略智能的压缩，再退回通用 head/tail。"""
    t = _preprocess_for_llm(text)
    if not t or len(t) <= max_chars:
        return t
    tn = (tool_name or "tool").lower()

    if tn in _SEARCH_TOOLS:
        blocks = [b.strip() for b in re.split(r"\n{2,}", t) if b.strip()]
        acc: list[str] = []
        used = 0
        for b in blocks[:16]:
            chunk = b if len(b) < 1200 else b[:1100] + "\n…(block truncated)"
            if used + len(chunk) + 2 > int(max_chars * 0.92):
                break
            acc.append(chunk)
            used += len(chunk) + 2
        merged = "\n\n".join(acc) if acc else t[:max_chars]
        if len(merged) <= max_chars:
            return merged
        return _hard_truncate(merged, max_chars, tn)

    if tn in _FILE_TOOLS:
        head = int(max_chars * 0.72)
        tail = max_chars - head - 80
        if tail < 120:
            tail = 120
            head = max(200, max_chars - tail - 80)
        omitted = max(0, len(t) - head - tail)
        return f"[{tn} truncated {omitted} chars]\n" + t[:head] + "\n…\n" + t[-tail:]

    if tn in _DB_TOOLS:
        lines = t.split("\n")
        head_lines = lines[:45]
        rest = "\n".join(lines[45:])
        head_txt = "\n".join(head_lines)
        if len(head_txt) + 40 <= max_chars:
            budget = max_chars - len(head_txt) - 30
            if rest and budget > 80:
                tail = rest[-budget:] if len(rest) > budget else rest
                return head_txt + "\n…\n" + tail
        return compress_for_llm(t, max_chars, tn)

    return compress_for_llm(t, max_chars, tn)
