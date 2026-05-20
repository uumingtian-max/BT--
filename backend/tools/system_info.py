"""系统硬件信息检测工具（Windows / Linux / macOS）。"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from typing import Any

import psutil


def _run_powershell(command: str, *, timeout: int = 10) -> str:
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(err or f"exit {proc.returncode}")
    return proc.stdout.strip()


def get_system_info(params: dict[str, Any]) -> str:
    """检测 CPU、GPU、内存、磁盘、系统版本等硬件信息。"""
    _ = params
    info: dict[str, Any] = {}

    info["os"] = f"{platform.system()} {platform.release()} {platform.version()}"
    info["machine"] = platform.machine()

    try:
        if sys.platform == "win32":
            out = _run_powershell(
                "Get-CimInstance Win32_Processor | "
                "Select-Object -First 1 Name,NumberOfCores,MaxClockSpeed | "
                "ForEach-Object { $_.Name + ' | cores=' + $_.NumberOfCores + ' | max_mhz=' + $_.MaxClockSpeed }"
            )
            info["cpu"] = out or "未知"
        else:
            out = subprocess.check_output(
                "lscpu | grep -E 'Model name|CPU\\(s\\)|MHz'",
                shell=True,
                text=True,
                timeout=5,
            )
            info["cpu"] = out.strip()
    except Exception as e:
        try:
            info["cpu"] = (
                f"{psutil.cpu_count(logical=False)} 物理核 / {psutil.cpu_count()} 逻辑核"
            )
        except Exception:
            info["cpu"] = f"获取失败: {e}"

    try:
        vm = psutil.virtual_memory()
        info["memory"] = f"共 {vm.total // (1024**3)} GB，已用 {vm.percent:.1f}%"
    except Exception as e:
        info["memory"] = f"获取失败: {e}"

    try:
        gpus: list[str] = []
        if sys.platform == "win32":
            try:
                out = _run_powershell(
                    "Get-CimInstance Win32_VideoController | "
                    "Select-Object Name,AdapterRAM,DriverVersion | "
                    "ForEach-Object { "
                    "$vram = if ($_.AdapterRAM) { [math]::Round($_.AdapterRAM/1GB,1).ToString() + 'GB' } else { 'n/a' }; "
                    "$_.Name + ' (显存约 ' + $vram + ', driver ' + $_.DriverVersion + ')' "
                    "}"
                )
                if out:
                    gpus.extend([ln.strip() for ln in out.splitlines() if ln.strip()])
            except Exception as exc:
                gpus.append(f"WMI: {exc}")
            try:
                proc = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,memory.total,driver_version",
                        "--format=csv,noheader",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    gpus.extend([f"NVIDIA-SMI: {ln.strip()}" for ln in proc.stdout.strip().splitlines()])
            except FileNotFoundError:
                pass
            info["gpu"] = gpus if gpus else "未检测到显卡"
        else:
            try:
                out = subprocess.check_output(
                    "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader",
                    shell=True,
                    text=True,
                    timeout=5,
                )
                info["gpu"] = out.strip().splitlines()
            except Exception:
                out = subprocess.check_output(
                    "lspci | grep -iE 'VGA|3D|Display'",
                    shell=True,
                    text=True,
                    timeout=5,
                )
                info["gpu"] = out.strip() or "未检测到显卡"
    except Exception as e:
        info["gpu"] = f"获取失败: {e}"

    try:
        disks: list[str] = []
        for part in psutil.disk_partitions(all=False):
            if sys.platform == "win32" and not part.mountpoint.endswith(":\\"):
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    f"{part.mountpoint} 总计{usage.total // (1024**3)}GB "
                    f"剩余{usage.free // (1024**3)}GB 已用{usage.percent:.1f}%"
                )
            except PermissionError:
                continue
        info["disk"] = disks if disks else "未检测到磁盘"
    except Exception as e:
        info["disk"] = f"获取失败: {e}"

    return json.dumps(info, ensure_ascii=False, indent=2)
