"""GPU 实时状态监控（nvidia-smi + 可选 pynvml）。"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


def _query_nvidia_smi() -> list[dict[str, str]]:
    proc = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,"
            "temperature.gpu,power.draw,power.limit",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "nvidia-smi failed").strip())
    gpus: list[dict[str, str]] = []
    for line in proc.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 8:
            continue
        try:
            used = int(float(parts[3]))
            total = int(float(parts[4]))
            free_mb = max(0, total - used)
        except ValueError:
            used, total, free_mb = parts[3], parts[4], "?"
        gpus.append(
            {
                "index": parts[0],
                "name": parts[1],
                "utilization": f"{parts[2]}%",
                "memory_used": f"{parts[3]} MB",
                "memory_total": f"{parts[4]} MB",
                "memory_free": f"{free_mb} MB" if free_mb != "?" else "?",
                "temperature": f"{parts[5]}°C",
                "power_draw": f"{parts[6]} W",
                "power_limit": f"{parts[7]} W",
            }
        )
    return gpus


def _query_pynvml() -> list[dict[str, str]]:
    import pynvml  # type: ignore[import-untyped]

    pynvml.nvmlInit()
    try:
        count = pynvml.nvmlDeviceGetCount()
        gpus: list[dict[str, str]] = []
        for i in range(count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode("utf-8", errors="replace")
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except Exception:
                temp = "?"
            try:
                power = pynvml.nvmlDeviceGetPowerUsage(handle) // 1000
                power_lim = pynvml.nvmlDeviceGetPowerManagementLimit(handle) // 1000
            except Exception:
                power, power_lim = "?", "?"
            used_mb = mem.used // (1024**2)
            total_mb = mem.total // (1024**2)
            gpus.append(
                {
                    "index": str(i),
                    "name": str(name),
                    "utilization": f"{util.gpu}%",
                    "memory_used": f"{used_mb} MB",
                    "memory_total": f"{total_mb} MB",
                    "memory_free": f"{max(0, total_mb - used_mb)} MB",
                    "temperature": f"{temp}°C",
                    "power_draw": f"{power} W",
                    "power_limit": f"{power_lim} W",
                }
            )
        return gpus
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass


def get_gpu_status(params: dict[str, Any]) -> str:
    """获取 GPU 实时状态：利用率、显存、温度、功耗。"""
    _ = params
    errors: list[str] = []

    try:
        gpus = _query_nvidia_smi()
        return json.dumps({"ok": True, "gpus": gpus, "source": "nvidia-smi"}, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        errors.append("nvidia-smi 未安装或不在 PATH")
    except Exception as exc:
        errors.append(f"nvidia-smi: {exc}")

    try:
        gpus = _query_pynvml()
        return json.dumps({"ok": True, "gpus": gpus, "source": "pynvml"}, ensure_ascii=False, indent=2)
    except ImportError:
        errors.append("pynvml 未安装（可选: pip install nvidia-ml-py）")
    except Exception as exc:
        errors.append(f"pynvml: {exc}")

    if sys.platform == "win32":
        try:
            from observe import get_hardware_snapshot

            return json.dumps(
                {
                    "ok": False,
                    "gpus": [],
                    "errors": errors,
                    "fallback": get_hardware_snapshot(),
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception:
            pass

    return json.dumps({"ok": False, "gpus": [], "errors": errors}, ensure_ascii=False, indent=2)


def optimize_gpu_memory(params: dict[str, Any]) -> str:
    """尝试释放 GPU 显存（CUDA 缓存清理）。"""
    _ = params
    try:
        import gc

        import torch

        gc.collect()
        if not torch.cuda.is_available():
            return json.dumps(
                {"status": "skip", "message": "torch 不可用或无 CUDA 设备"},
                ensure_ascii=False,
            )
        torch.cuda.empty_cache()
        if hasattr(torch.cuda, "ipc_collect"):
            torch.cuda.ipc_collect()
        return json.dumps(
            {
                "status": "success",
                "message": "已执行 torch.cuda.empty_cache()",
                "allocated_mb": torch.cuda.memory_allocated() // (1024**2),
                "reserved_mb": torch.cuda.memory_reserved() // (1024**2),
            },
            ensure_ascii=False,
            indent=2,
        )
    except ImportError:
        return json.dumps(
            {
                "status": "skip",
                "message": "未安装 torch；可关闭占用 GPU 的进程或重启 Ollama/vLLM 释放显存",
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)
