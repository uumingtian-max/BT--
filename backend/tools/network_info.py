"""网络状态：带宽采样、连接与端口占用。"""

from __future__ import annotations

import json
import socket
from typing import Any


def get_network_status(params: dict[str, Any]) -> str:
    """
    获取网络状态摘要。

    params:
        include_connections: 是否列出连接（默认 true，最多 40 条）
        port: 若指定则筛选占用该端口的进程
    """
    include_conn = params.get("include_connections", True)
    port_filter = params.get("port")
    if port_filter is not None:
        port_filter = int(port_filter)

    out: dict[str, Any] = {"ok": True}

    try:
        import psutil

        io1 = psutil.net_io_counters()
        out["io_counters"] = {
            "bytes_sent_mb": round(io1.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(io1.bytes_recv / (1024**2), 2),
            "packets_sent": io1.packets_sent,
            "packets_recv": io1.packets_recv,
        }
        try:
            addrs = psutil.net_if_addrs()
            ifaces: list[dict[str, str]] = []
            for name, snics in list(addrs.items())[:12]:
                for snic in snics:
                    if snic.family == socket.AF_INET:
                        ifaces.append({"iface": name, "ipv4": snic.address})
                        break
            out["interfaces"] = ifaces[:12]
        except Exception as exc:
            out["interfaces_error"] = str(exc)

        if include_conn:
            rows: list[dict[str, Any]] = []
            for conn in psutil.net_connections(kind="inet"):
                try:
                    lport = conn.laddr.port if conn.laddr else None
                    if port_filter is not None and lport != port_filter:
                        continue
                    pid = conn.pid or 0
                    pname = ""
                    if pid:
                        try:
                            pname = psutil.Process(pid).name()
                        except Exception:
                            pname = "?"
                    rows.append(
                        {
                            "pid": pid,
                            "process": pname,
                            "status": conn.status,
                            "local": f"{conn.laddr.ip}:{lport}" if conn.laddr else "",
                            "remote": (
                                f"{conn.raddr.ip}:{conn.raddr.port}"
                                if conn.raddr
                                else ""
                            ),
                        }
                    )
                except Exception:
                    continue
                if len(rows) >= 40:
                    break
            out["connections"] = rows
            if port_filter is not None:
                out["port_filter"] = port_filter
                out["port_listeners"] = [r for r in rows if r.get("status") == "LISTEN"]
    except ImportError as exc:
        out = {"ok": False, "error": f"psutil required: {exc}"}
    except Exception as exc:
        out = {"ok": False, "error": str(exc)}

    return json.dumps(out, ensure_ascii=False, indent=2)
