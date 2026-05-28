"""
上下文压缩模块 — BT黑光本地版
策略：
  1. 预处理（去HTML/缩URL/去base64）
  2. 短文本直接返回
  3. 中等文本 head/tail 截断
  4. 超长文本 → 调 sglang 摘要压缩（失败自动降级为截断）
  5. API备用通道（sglang不可用时自动切换）
模型优先级：sglang:8001 → API(OPENAI_BASE_URL) → 纯截断
"""
from __future__ import annotations

import os
import re
import json
import logging
import httpx
from typing import Match

_logger = logging.getLogger(__name__)

# ─────────────────────────── 配置 ───────────────────────────
SGLANG_BASE = os.environ.get("SGLANG_BASE_URL", "http://127.0.0.1:8001/v1")
API_BASE     = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8001/v1")
API_KEY      = os.environ.get("OPENAI_API_KEY", "sk-local")

# 超过此字符数才尝试摘要（避免小文本浪费推理资源）
SUMMARY_THRESHOLD = 3000
# 摘要目标长度（字符数）
SUMMARY_TARGET    = 800
# 推理超时秒数
INFER_TIMEOUT     = 18

# ─────────────────────────── 正则 ───────────────────────────
_TAG_RE      = re.compile(r"<[^>]{0,500}?>", re.DOTALL)
_URL_RE      = re.compile(r"https?://[^\s)\]>\"\']{8,500}")
_DATA_URI_RE = re.compile(r"data:[^,\s]+,[A-Za-z0-9+/=\s]{80,}", re.IGNORECASE)
_WS_RE       = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n{3,}")

_SEARCH_TOOLS = frozenset({"web_search", "local_search"})
_FILE_TOOLS   = frozenset({"read_file", "list_files", "write_file"})
_DB_TOOLS     = frozenset({"query_database"})


# ─────────────────────────── 基础工具 ───────────────────────────
def _short_url(m: Match[str]) -> str:
    u = m.group(0)
    return u if len(u) <= 48 else u[:32] + "…" + u[-10:]


def _preprocess(text: str) -> str:
    if not text:
        return ""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = _TAG_RE.sub(" ", t)
    t = _URL_RE.sub(_short_url, t)
    t = _DATA_URI_RE.sub("[base64 omitted]", t)
    t = _WS_RE.sub(" ", t)
    return _BLANK_LINES.sub("\n\n", t).strip()


def _hard_truncate(t: str, max_chars: int, note: str = "") -> str:
    prefix_est = (len(note) + 36) if note else 24
    body_budget = max(80, max_chars - prefix_est - 16)
    head = body_budget // 2
    tail = max(40, body_budget - head)
    head = max(40, body_budget - tail)
    omitted = max(0, len(t) - head - tail)
    prefix = f"[{note} truncated {omitted} chars]\n" if note else f"[truncated {omitted} chars]\n"
    return prefix + t[:head] + "\n…\n" + t[-tail:]


# ─────────────────────────── 摘要推理 ───────────────────────────
def _call_summarize(text: str, target_chars: int, note: str) -> str | None:
    """
    调用本地sglang或API做摘要压缩。
    返回摘要字符串，失败返回None（调用方降级为截断）。
    """
    sys_prompt = (
        "你是一个文本压缩专家。请将用户提供的内容压缩为简洁摘要，"
        f"保留所有关键信息、数字、结论，目标长度约{target_chars}字符以内。"
        "直接输出摘要内容，不加任何解释。"
    )
    user_prompt = f"请压缩以下{note}内容：\n\n{text[:12000]}"

    # 尝试 sglang 端点
    for base_url in [SGLANG_BASE, API_BASE]:
        try:
            resp = httpx.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": _get_model(base_url),
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": max(256, target_chars // 2),
                    "temperature": 0.1,
                },
                timeout=INFER_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            summary = data["choices"][0]["message"]["content"].strip()
            if summary:
                return f"[{note} AI摘要]\n{summary}"
        except Exception as e:
            _logger.debug("摘要推理失败 base=%s err=%s", base_url, e)
            continue
    return None


def _get_model(base_url: str) -> str:
    """从端点获取第一个可用模型名，失败返回默认值。"""
    try:
        resp = httpx.get(f"{base_url}/models", timeout=3)
        models = resp.json().get("data", [])
        if models:
            return models[0]["id"]
    except Exception:
        pass
    return os.environ.get("AGENT_DEFAULT_MODEL", "default")


# ─────────────────────────── 主接口 ───────────────────────────
def compress_for_llm(text: str, max_chars: int, note: str = "") -> str:
    """
    通用压缩入口。
    短文本直接返回；超过 SUMMARY_THRESHOLD 且 max_chars 足够大时尝试AI摘要；
    否则 head/tail 截断。
    """
    t = _preprocess(text)
    if not t:
        return ""
    if len(t) <= max_chars:
        return t

    # 超长且允许摘要
    if len(t) >= SUMMARY_THRESHOLD and max_chars >= 400:
        summary = _call_summarize(t, min(SUMMARY_TARGET, max_chars - 50), note or "content")
        if summary and len(summary) <= max_chars:
            return summary

    return _hard_truncate(t, max_chars, note)


def compress_tool_result_for_llm(text: str, max_chars: int, tool_name: str) -> str:
    """按工具类型智能压缩，超长时优先AI摘要，失败降级截断。"""
    t = _preprocess(text)
    if not t or len(t) <= max_chars:
        return t
    tn = (tool_name or "tool").lower()

    # 搜索结果：按段落聚合，保留最多16块
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
        # 超长再尝试摘要
        if len(merged) >= SUMMARY_THRESHOLD:
            summary = _call_summarize(merged, min(SUMMARY_TARGET, max_chars - 50), tn)
            if summary and len(summary) <= max_chars:
                return summary
        return _hard_truncate(merged, max_chars, tn)

    # 文件读取：头部优先，保留尾部
    if tn in _FILE_TOOLS:
        head = int(max_chars * 0.72)
        tail = max(120, max_chars - head - 80)
        head = max(200, max_chars - tail - 80)
        omitted = max(0, len(t) - head - tail)
        return f"[{tn} truncated {omitted} chars]\n" + t[:head] + "\n…\n" + t[-tail:]

    # 数据库查询：保留前45行
    if tn in _DB_TOOLS:
        lines = t.split("\n")
        head_txt = "\n".join(lines[:45])
        rest = "\n".join(lines[45:])
        if len(head_txt) + 40 <= max_chars:
            budget = max_chars - len(head_txt) - 30
            if rest and budget > 80:
                tail = rest[-budget:] if len(rest) > budget else rest
                return head_txt + "\n…\n" + tail
        return compress_for_llm(t, max_chars, tn)

    # 默认：尝试摘要 → 截断
    return compress_for_llm(t, max_chars, tn)


# ─────────────────────────── 滑动窗口对话压缩 ───────────────────────────
def compress_conversation_window(
    messages: list[dict],
    max_chars: int = 6000,
    keep_recent: int = 6,
) -> list[dict]:
    """
    对话历史滑动窗口压缩：
    - 保留最近 keep_recent 条完整消息
    - 更早的消息摘要合并为一条 system 消息
    - 总字符不超过 max_chars
    """
    if not messages:
        return messages

    recent = messages[-keep_recent:]
    older  = messages[:-keep_recent]

    if not older:
        return recent

    # 把旧消息拼成文本送去摘要
    older_text = "\n".join(
        f"{m.get('role','?')}: {m.get('content','')}" for m in older
    )

    summary_text = _call_summarize(
        older_text,
        target_chars=min(800, max_chars // 4),
        note="对话历史",
    )
    if not summary_text:
        # 降级：只保留最近消息
        return recent

    summary_msg = {
        "role": "system",
        "content": f"[早期对话摘要]\n{summary_text}",
    }
    return [summary_msg] + recent
