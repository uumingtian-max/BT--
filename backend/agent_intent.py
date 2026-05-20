"""Deterministic intent → tool mapping (shared by agent loop and task brief)."""

from __future__ import annotations

import re
from typing import Any

HARDWARE_PATTERNS: list[tuple[str, str]] = [
    (r"(显卡.*型号|什么显卡|哪张卡|GPU.*型号)", "get_system_info"),
    (r"(CPU|处理器|几核|主频)", "get_system_info"),
    (r"(内存|RAM|运行内存)", "get_system_info"),
    (r"(硬盘|磁盘|SSD|HDD|剩余空间)", "get_system_info"),
    (r"(电脑配置|硬件信息|系统信息|我的电脑)", "get_system_info"),
]

GPU_LIVE_PATTERNS: list[str] = [
    r"显存占用",
    r"显存使用",
    r"gpu\s*占用",
    r"gpu\s*负载",
    r"gpu\s*利用率",
    r"显卡温度",
    r"gpu\s*温度",
    r"多少度",
    r"功耗",
    r"实时.*gpu",
    r"5090",
]

VRAM_CLEAN_PATTERNS: list[str] = [
    r"清理显存",
    r"释放显存",
    r"显存碎片",
    r"清空.*cuda",
    r"gpu\s*内存.*清理",
]

NETWORK_PATTERNS: list[str] = [
    r"网络状态",
    r"网速",
    r"端口占用",
    r"谁占.*8000",
    r"8000.*端口",
    r"连接状态",
]

SEARCH_FILE_PATTERNS: list[str] = [
    r"搜索文件",
    r"找文件",
    r"查找.*\.(py|md|txt|json)",
    r"全盘搜索",
    r"文件名.*搜索",
]

PROCESS_LIST_PATTERNS: list[str] = [
    r"进程列表",
    r"哪些进程",
    r"占用最高",
    r"占内存最多",
    r"占cpu最多",
    r"tasklist",
]

KILL_PROCESS_PATTERNS: list[str] = [
    r"结束进程",
    r"杀掉进程",
    r"杀死进程",
    r"关闭进程",
    r"kill\s+process",
]


def infer_gpu_live_tool(user_msg: str) -> str | None:
    text = (user_msg or "").strip()
    if not text:
        return None
    if any(re.search(p, text, re.IGNORECASE) for p in VRAM_CLEAN_PATTERNS):
        return "optimize_gpu_memory"
    if any(re.search(p, text, re.IGNORECASE) for p in GPU_LIVE_PATTERNS):
        return "get_gpu_status"
    live_markers = ("利用率", "温度", "功耗", "实时")
    gpu_markers = ("gpu", "显卡", "显存", "5090", "nvidia")
    if any(m in text.lower() or m in text for m in gpu_markers) and any(
        m in text for m in live_markers
    ):
        return "get_gpu_status"
    return None


def extract_process_target(user_msg: str) -> dict[str, Any]:
    """Parse pid or process name from user text."""
    text = (user_msg or "").strip()
    out: dict[str, Any] = {}
    m = re.search(r"\bpid[:\s=]*(\d+)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"进程\s*[#№]?\s*(\d{2,6})", text)
    if m:
        out["pid"] = int(m.group(1))
    m = re.search(r'[「「"\']?([A-Za-z0-9_.-]+\.exe)[」」"\']?', text, re.IGNORECASE)
    if m and "pid" not in out:
        out["name"] = m.group(1)
    return out


def infer_process_tool(user_msg: str) -> str | None:
    text = (user_msg or "").strip()
    if not text:
        return None
    if any(re.search(p, text, re.IGNORECASE) for p in KILL_PROCESS_PATTERNS):
        target = extract_process_target(text)
        if target.get("pid") or target.get("name"):
            return "kill_process"
        return "get_process_list"
    if any(re.search(p, text, re.IGNORECASE) for p in PROCESS_LIST_PATTERNS):
        return "get_process_list"
    if "进程" in text and any(k in text for k in ("列表", "排名", "占用", "最高", "哪些")):
        return "get_process_list"
    return None


def build_inferred_tool_call(user_msg: str) -> dict[str, Any] | None:
    """Full tool_call dict from deterministic intent."""
    tool = infer_hardware_tool(user_msg)
    if not tool:
        return None
    params: dict[str, Any] = {}
    if tool == "get_process_list":
        text = user_msg.lower()
        params = {
            "top_n": 15,
            "sort_by": "cpu" if "cpu" in text else "memory",
        }
    elif tool == "kill_process":
        params = extract_process_target(user_msg)
        if not params:
            return {"name": "get_process_list", "parameters": {"top_n": 15, "sort_by": "memory"}}
    elif tool == "get_network_status":
        m = re.search(r"(\d{2,5})\s*端口|端口\s*(\d{2,5})", user_msg)
        if m:
            params["port"] = int(m.group(1) or m.group(2))
    elif tool == "search_files":
        params = {"query": user_msg, "directory": "desktop", "max_results": 40}
        ext_m = re.search(r"\.(py|md|txt|json|js|tsx?)", user_msg, re.I)
        if ext_m:
            params = {"extension": "." + ext_m.group(1).lower(), "directory": "project", "max_results": 50}
        qm = re.search(r"[「「\"']([^\"']+)[」」\"']", user_msg)
        if qm:
            params["query"] = qm.group(1)
    return {"name": tool, "parameters": params}


def infer_hardware_tool(user_msg: str) -> str | None:
    """Return tool name when message is a hardware/spec query (not perf tuning)."""
    text = (user_msg or "").strip()
    if not text:
        return None
    gpu_live = infer_gpu_live_tool(text)
    if gpu_live:
        return gpu_live
    if any(re.search(p, text, re.IGNORECASE) for p in NETWORK_PATTERNS):
        port = None
        m = re.search(r"(\d{2,5})\s*端口|端口\s*(\d{2,5})", text)
        if m:
            port = int(m.group(1) or m.group(2))
        return "get_network_status" if port is None else "get_network_status"

    if any(re.search(p, text, re.IGNORECASE) for p in SEARCH_FILE_PATTERNS):
        return "search_files"

    proc = infer_process_tool(text)
    if proc:
        return proc
    perf_markers = ("优化", "性能", "卡顿", "慢")
    if any(m in text for m in perf_markers):
        if any(k in text for k in ("显存", "gpu", "显卡", "5090")):
            return "get_gpu_status"
        return None
    if any(m in text for m in ("占用", "负载")) and any(
        k in text.lower() or k in text for k in ("gpu", "显卡", "显存")
    ):
        return "get_gpu_status"
    for pattern, tool in HARDWARE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return tool
    if re.search(r"(显卡|GPU|显存)", text, re.IGNORECASE) and not any(
        m in text for m in perf_markers
    ):
        return "get_system_info"
    return None


def extract_shell_command(message: str) -> str | None:
    """Pull an explicit shell/git/npm/pytest command from user text."""
    text = (message or "").strip()
    if not text:
        return None

    for pattern in (
        r"```(?:bash|sh|shell|powershell|ps1|cmd)?\s*([\s\S]+?)```",
        r"`([^`]{3,400})`",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate and not candidate.startswith("{"):
                return candidate

    lower = text.lower()
    git_verbs = ("status", "add", "commit", "push", "pull", "fetch", "log", "diff", "branch", "checkout", "merge")
    if "git" in lower:
        for verb in git_verbs:
            if verb in lower or verb in text:
                m = re.search(rf"\bgit\s+{verb}(?:\s+[^\n。；;]+)?", text, re.IGNORECASE)
                if m:
                    return m.group(0).strip()
        if any(k in text for k in ("提交", "推送", "拉取", "合并", "仓库状态")):
            if "提交" in text or "commit" in lower:
                return "git status"
            if "推送" in text or "push" in lower:
                return "git push"
            if "拉取" in text or "pull" in lower:
                return "git pull"
            return "git status"

    if any(k in lower for k in ("pytest", "npm run", "npm test", "ruff check", "pip install")):
        m = re.search(
            r"(pytest[^\n。；;]*|npm\s+(?:run|test|install)[^\n。；;]*|ruff\s+check[^\n。；;]*|pip\s+install[^\n。；;]*)",
            text,
            re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()

    run_markers = ("运行", "执行", "跑一下", "跑下", "命令", "终端", "shell", "powershell", "cmd")
    if any(k in text or k in lower for k in run_markers):
        m = re.search(
            r"(?:运行|执行|命令[：:])\s*[`\"']?([^\n。；;`\"']{3,300})",
            text,
            re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()

    return None


def looks_like_action_request(message: str) -> bool:
    triggers = (
        "帮我",
        "给我",
        "直接",
        "马上",
        "立刻",
        "看看",
        "读取",
        "打开",
        "列出",
        "查一下",
        "搜索",
        "总结",
        "分析",
        "整理",
        "写入",
        "创建",
        "执行",
        "运行",
        "生成",
        "提交",
        "推送",
        "拉取",
        "合并",
        "删除",
        "修改",
        "修复",
        "检查",
        "测试",
        "构建",
        "部署",
        "安装",
        "配置",
        "git",
        "npm",
        "pytest",
    )
    return any(token in message for token in triggers)


def looks_like_options_only(text: str) -> bool:
    """Model gave choices instead of acting."""
    lowered = (text or "").lower()
    markers = (
        "你可以",
        "您可以",
        "建议你",
        "推荐你",
        "方法一",
        "方法二",
        "选项",
        "以下方式",
        "以下几种",
        "如果需要",
        "请告诉我",
        "你想",
        "您想",
        "要不要",
        "是否需要",
        "option a",
        "option b",
    )
    return sum(1 for m in markers if m in text or m in lowered) >= 2
