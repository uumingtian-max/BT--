"""Chat prefetch must inject hardware facts, not allow hallucination path."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from chat_action_prefetch import (  # noqa: E402
    looks_like_hardware_or_perf_query,
    prefetch_facts_for_chat,
)


def test_hardware_query_detected():
    assert looks_like_hardware_or_perf_query("我显卡什么型号的")


def test_prefetch_contains_hardware_section():
    block = prefetch_facts_for_chat("我显卡什么型号的")
    assert "本机实测" in block or "硬件实测" in block or "硬件" in block
