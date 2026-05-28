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
API_KEY=os.env...Y", "sk-local")

# 超过此字符数才尝试摘要（避免小文本浪费推理资源）
SUMMARY_THRESHOLD = 3000
# 摘要目标长度（字符数）
SUMMARY_TARGET    = 800
# 推理超时秒数
INFER_TIMEOUT     = 18

# ─────────────────────────── 正则 ───────────────────────────
_TAG_RE      = re.compile(r"<[^>]{0,500}?>", re.DOTALL)
_URL_RE      = re.compile(r"https?://[^\s)\]>\"\]{8,500}")
_DATA_URI_RE = re.compile(r"data:[^,\s]+,[A-Za-z0-9+/=\s]{80,}", re.IGNORECASE)
_WS_RE       = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n{3,}")

_SEARCH_TOOLS = frozenset({"web_search", "local_search"})
_FILE_TOOLS   = frozenset({"read_file", "list_files", "write_file"})
_DB_TOOLS     = frozenset({"query_database"})

