"""
context_pack.py — BT黑光 上下文压缩模块
sglang:8001 主力 + API备用 + 纯截断兜底
"""
from __future__ import annotations
import os, re, logging
from typing import Match
import httpx

_logger = logging.getLogger(__name__)

SGLANG_BASE = os.environ.get("SGLANG_BASE_URL", "http://127.0.0.1:8001/v1")
API_BASE    = os.environ.get("OPENAI_BASE_URL",  "http://127.0.0.1:8001/v1")
API_KEY     = os.environ.get("OPENAI_API_KEY",   "sk-local")
SUMMARY_THRESHOLD = 3000
SUMMARY_TARGET    = 800
INFER_TIMEOUT     = 18

_TAG_RE      = re.compile(r"<[^>]{0,500}?>", re.DOTALL)
_URL_RE      = re.compile(r"https?://[^\s)\]>\"']{8,500}")
_DATA_URI_RE = re.compile(r"data:[^,\s]+,[A-Za-z0-9+/=\s]{80,}", re.IGNORECASE)
_WS_RE       = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n{3,}")
_SEARCH_TOOLS = frozenset({"web_search","local_search"})
_FILE_TOOLS   = frozenset({"read_file","list_files","write_file"})
_DB_TOOLS     = frozenset({"query_database"})

def _short_url(m: Match) -> str:
    u = m.group(0)
    return u if len(u) <= 48 else u[:32] + "..." + u[-10:]

def _preprocess(text: str) -> str:
    if not text: return ""
    t = text.replace("\r\n","\n").replace("\r","\n")
    t = _TAG_RE.sub(" ", t)
    t = _URL_RE.sub(_short_url, t)
    t = _DATA_URI_RE.sub("[base64 omitted]", t)
    t = _WS_RE.sub(" ", t)
    return _BLANK_LINES.sub("\n\n", t).strip()

def _hard_truncate(t: str, max_chars: int, note: str = "") -> str:
    body = max(80, max_chars - (len(note)+36 if note else 24) - 16)
    head = body // 2
    tail = max(40, body - head)
    head = max(40, body - tail)
    omitted = max(0, len(t) - head - tail)
    prefix = f"[{note} truncated {omitted} chars]\n" if note else f"[truncated {omitted} chars]\n"
    return prefix + t[:head] + "\n...\n" + t[-tail:]

def _get_model(base_url: str) -> str:
    try:
        r = httpx.get(f"{base_url}/models", timeout=3)
        data = r.json().get("data", [])
        if data: return data[0]["id"]
    except: pass
    return os.environ.get("AGENT_DEFAULT_MODEL", "default")

def _call_summarize(text: str, target_chars: int, note: str) -> str | None:
    sys_p = (f"你是文本压缩专家。将内容压缩为简洁摘要，保留关键信息、数字、结论，"
             f"目标{target_chars}字符以内。直接输出摘要，不加解释。")
    user_p = f"压缩以下{note}内容：\n\n{text[:12000]}"
    for base in [SGLANG_BASE, API_BASE]:
        try:
            r = httpx.post(f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={"model": _get_model(base),
                      "messages": [{"role":"system","content":sys_p},
                                   {"role":"user","content":user_p}],
                      "max_tokens": max(256, target_chars//2),
                      "temperature": 0.1},
                timeout=INFER_TIMEOUT)
            r.raise_for_status()
            s = r.json()["choices"][0]["message"]["content"].strip()
            if s: return f"[{note} AI摘要]\n{s}"
        except Exception as e:
            _logger.debug("摘要失败 base=%s err=%s", base, e)
    return None

def compress_for_llm(text: str, max_chars: int, note: str = "") -> str:
    t = _preprocess(text)
    if not t: return ""
    if len(t) <= max_chars: return t
    if len(t) >= SUMMARY_THRESHOLD and max_chars >= 400:
        s = _call_summarize(t, min(SUMMARY_TARGET, max_chars-50), note or "content")
        if s and len(s) <= max_chars: return s
    return _hard_truncate(t, max_chars, note)

def compress_tool_result_for_llm(text: str, max_chars: int, tool_name: str) -> str:
    t = _preprocess(text)
    if not t or len(t) <= max_chars: return t
    tn = (tool_name or "tool").lower()
    if tn in _SEARCH_TOOLS:
        blocks = [b.strip() for b in re.split(r"\n{2,}", t) if b.strip()]
        acc, used = [], 0
        for b in blocks[:16]:
            chunk = b if len(b) < 1200 else b[:1100] + "\n...(truncated)"
            if used + len(chunk) + 2 > int(max_chars * 0.92): break
            acc.append(chunk); used += len(chunk) + 2
        merged = "\n\n".join(acc) if acc else t[:max_chars]
        if len(merged) <= max_chars: return merged
        if len(merged) >= SUMMARY_THRESHOLD:
            s = _call_summarize(merged, min(SUMMARY_TARGET, max_chars-50), tn)
            if s and len(s) <= max_chars: return s
        return _hard_truncate(merged, max_chars, tn)
    if tn in _FILE_TOOLS:
        head = int(max_chars * 0.72)
        tail = max(120, max_chars - head - 80)
        head = max(200, max_chars - tail - 80)
        omitted = max(0, len(t) - head - tail)
        return f"[{tn} truncated {omitted} chars]\n" + t[:head] + "\n...\n" + t[-tail:]
    if tn in _DB_TOOLS:
        lines = t.split("\n")
        head_txt = "\n".join(lines[:45])
        rest = "\n".join(lines[45:])
        if len(head_txt) + 40 <= max_chars:
            budget = max_chars - len(head_txt) - 30
            if rest and budget > 80:
                return head_txt + "\n...\n" + (rest[-budget:] if len(rest) > budget else rest)
        return compress_for_llm(t, max_chars, tn)
    return compress_for_llm(t, max_chars, tn)

def compress_conversation_window(messages: list, max_chars: int = 6000, keep_recent: int = 6) -> list:
    if not messages: return messages
    recent = messages[-keep_recent:]
    older  = messages[:-keep_recent]
    if not older: return recent
    older_text = "\n".join(f"{m.get('role','?')}: {m.get('content','')}" for m in older)
    summary = _call_summarize(older_text, min(800, max_chars//4), "对话历史")
    if not summary: return recent
    return [{"role":"system","content":f"[早期对话摘要]\n{summary}"}] + recent
