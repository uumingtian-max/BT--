"""进程管理工具（列表 / 结束进程）。"""

from __future__ import annotations

import json
import platform
import subprocess
from typing import Any

_PROTECTED_NAMES = frozenset(
    {
        "system",
        "system idle process",
        "registry",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "smss.exe",
        "winlogon.exe",
        "dwm.exe",
        "explorer.exe",
    }
)


def _sort_key(proc: dict[str, str], sort_by: str) -> float:
    key = "memory" if sort_by == "memory" else "cpu"
    raw = proc.get(key, "0").replace(" MB", "").replace("%", "").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.0


def get_process_list(params: dict[str, Any]) -> str:
    """
    获取进程列表，按 CPU 或内存排序。

    params:
        top_n: 返回前 N 个，默认 15
        sort_by: cpu | memory，默认 memory
    """
    top_n = max(1, min(50, int(params.get("top_n", 15) or 15)))
    sort_by = str(params.get("sort_by", "memory") or "memory").lower()
    if sort_by not in ("cpu", "memory"):
        sort_by = "memory"

    try:
        import psutil

        psutil.cpu_percent(interval=0.1)
        procs: list[dict[str, Any]] = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
            try:
                info = p.info
                mi = info.get("memory_info")
                rss_mb = (mi.rss // (1024**2)) if mi else 0
                procs.append(
                    {
                        "pid": info.get("pid"),
                        "name": info.get("name") or "?",
                        "cpu": f"{(info.get('cpu_percent') or 0):.1f}%",
                        "memory": f"{rss_mb} MB",
                        "status": info.get("status") or "?",
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        procs.sort(key=lambda row: _sort_key(row, sort_by), reverse=True)
        return json.dumps(procs[:top_n], ensure_ascii=False, indent=2)
    except ImportError:
        pass

    if platform.system() == "Windows":
        out = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        text = (out.stdout or "")[:3000]
        return text or "tasklist 无输出"
    out = subprocess.run(
        ["/bin/sh", "-lc", f"ps aux --sort=-%mem | head -n {top_n + 1}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    return (out.stdout or out.stderr or "")[:3000]


def kill_process(params: dict[str, Any]) -> str:
    """
    结束进程。

    params:
        pid: 进程 ID（优先）
        name: 进程名（pid 为空时按名称匹配，可能结束多个）
        force: 为 true 时用 kill 而非 terminate
    """
    pid_raw = params.get("pid")
    name = str(params.get("name") or "").strip()
    force = bool(params.get("force"))

    try:
        import psutil

        if pid_raw is not None and str(pid_raw).strip():
            pid = int(pid_raw)
            if pid <= 4:
                return json.dumps(
                    {"status": "policy_denied", "message": f"拒绝结束系统关键 PID={pid}"},
                    ensure_ascii=False,
                )
            p = psutil.Process(pid)
            pname = p.name()
            if pname.lower() in _PROTECTED_NAMES:
                return json.dumps(
                    {"status": "policy_denied", "message": f"拒绝结束受保护进程 {pname}"},
                    ensure_ascii=False,
                )
            if force:
                p.kill()
            else:
                p.terminate()
            return json.dumps(
                {"status": "success", "message": f"已结束 {pname} (pid={pid})"},
                ensure_ascii=False,
            )

        if name:
            if name.lower() in _PROTECTED_NAMES:
                return json.dumps(
                    {"status": "policy_denied", "message": f"拒绝结束受保护进程 {name}"},
                    ensure_ascii=False,
                )
            killed: list[int] = []
            for p in psutil.process_iter(["pid", "name"]):
                try:
                    if (p.info.get("name") or "").lower() == name.lower():
                        if force:
                            p.kill()
                        else:
                            p.terminate()
                        killed.append(int(p.info["pid"]))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if killed:
                return json.dumps(
                    {
                        "status": "success",
                        "message": f"已结束 {name}，pid={killed}",
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {"status": "not_found", "message": f"未找到进程 {name}"},
                ensure_ascii=False,
            )

        return json.dumps(
            {"status": "error", "message": "需要 pid 或 name 参数"},
            ensure_ascii=False,
        )
    except Exception as exc:
        err_name = type(exc).__name__
        if err_name == "NoSuchProcess":
            return json.dumps({"status": "not_found", "message": "进程不存在"}, ensure_ascii=False)
        return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)
