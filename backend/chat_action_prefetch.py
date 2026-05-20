"""Chat 模式下的工具预取：无工具链时也能注入本机实测，避免编造硬件/性能数据。"""

from __future__ import annotations

import re


_HARDWARE_MARKERS = (
    "显卡",
    "gpu",
    "graphics",
    "nvidia",
    "amd",
    "显存",
    "vram",
    "5090",
    "4090",
    "1650",
    "性能",
    "优化",
    "cpu",
    "内存",
    "ram",
    "硬盘",
    "磁盘",
    "温度",
    "占用",
    "负载",
    "卡顿",
    "慢",
    "硬件",
    "配置",
    "电脑配置",
    "什么型号",
    "什么卡",
)

_ACTION_MARKERS = (
    "帮我",
    "给我",
    "去",
    "执行",
    "运行",
    "检查",
    "看看",
    "查",
    "优化",
    "整理",
    "修复",
    "安装",
    "启动",
    "关闭",
    "删除",
    "提交",
    "推送",
)


def looks_like_hardware_or_perf_query(message: str) -> bool:
    text = (message or "").strip()
    lower = text.lower()
    return any(m in text or m in lower for m in _HARDWARE_MARKERS)


def looks_like_action_in_chat(message: str) -> bool:
    text = (message or "").strip()
    if looks_like_hardware_or_perf_query(text):
        return True
    return any(m in text for m in _ACTION_MARKERS)


def prefetch_facts_for_chat(message: str) -> str:
    """Run safe read-only tools and return text block for system prompt."""
    text = (message or "").strip()
    if not text:
        return ""

    blocks: list[str] = []

    try:
        from observe import format_profile_for_llm, get_hardware_snapshot

        blocks.append(format_profile_for_llm())
        if looks_like_hardware_or_perf_query(text):
            blocks.append(get_hardware_snapshot())
    except Exception as exc:
        blocks.append(f"【设备采集失败】{exc}")

    if looks_like_hardware_or_perf_query(text) or any(k in text for k in ("优化", "性能", "卡顿")):
        try:
            from tools.gpu_monitor import get_gpu_status

            blocks.append(get_gpu_status({}))
        except Exception as exc:
            blocks.append(f"【GPU 状态失败】{exc}")
        if any(k in text for k in ("进程", "占用最高")):
            try:
                from tools.process_info import get_process_list

                blocks.append(get_process_list({"top_n": 10, "sort_by": "memory"}))
            except Exception as exc:
                blocks.append(f"【进程列表失败】{exc}")

    if not blocks:
        return ""

    body = "\n\n".join(blocks)
    return (
        "【本机实测数据·回答必须仅依据以下内容，禁止编造型号/占用/温度】\n"
        + body
        + "\n\n若实测区无显卡型号，必须回答「当前未采集到」，禁止猜测 GTX/RTX 等型号。"
    )


def should_nudge_agent_mode(message: str) -> bool:
    """Messages that need tool execution beyond read-only prefetch."""
    text = (message or "").strip()
    if re.search(r"\bgit\s+\w+", text, re.I):
        return True
    if any(k in text for k in ("写入", "删除", "安装", "部署", "构建", "pytest", "npm run")):
        return True
    return False
