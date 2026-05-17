"""
Telegraf-friendly metrics (Prometheus exposition text).

Scrape with Telegraf [[inputs.prometheus]] → forward e.g. to InfluxDB, aligning local-first
observability (OpenHuman-style) + durable task signals (agentmemory-style) + multi-signal
pipelines (RuView-style: many inputs, one export path — without any WiFi/CSI coupling).
"""

from __future__ import annotations

import os
import re
from typing import Any

from fastapi import APIRouter, Response

from observe import telemetry_export_snapshot

router = APIRouter(prefix="/telegraf", tags=["telegraf"])

_LABEL_SAFE = re.compile(r"[^a-zA-Z0-9_]")


def _enabled() -> bool:
    return os.environ.get("TELEGRAF_METRICS", "1").strip().lower() not in ("0", "false", "off", "no")


def _label(s: str) -> str:
    t = _LABEL_SAFE.sub("_", (s or "").strip())[:64] or "unknown"
    if t[0].isdigit():
        t = "x_" + t
    return t


def _prometheus_lines(data: dict[str, Any]) -> list[str]:
    lines: list[str] = [
        "# HELP agent_backend_up Backend HTTP process is up (1) or metrics disabled (0).",
        "# TYPE agent_backend_up gauge",
    ]
    if not _enabled():
        lines.append("agent_backend_up 0")
        lines.append(
            "# HELP agent_telegraf_metrics_disabled Telegraf scrape disabled via TELEGRAF_METRICS=0."
        )
        lines.append("# TYPE agent_telegraf_metrics_disabled gauge")
        lines.append("agent_telegraf_metrics_disabled 1")
        return lines

    lines.append("agent_backend_up 1")
    lines.append("agent_telegraf_metrics_disabled 0")

    w24 = data.get("window_24h") or {}
    ts = int(w24.get("total_success") or 0)
    tf = int(w24.get("total_fail") or 0)
    lines += [
        "# HELP agent_task_outcomes_total_24h Count of recorded task outcomes in last 24h.",
        "# TYPE agent_task_outcomes_total_24h gauge",
        f'agent_task_outcomes_total_24h{{status="success"}} {ts}',
        f'agent_task_outcomes_total_24h{{status="failed"}} {tf}',
    ]

    by_type = w24.get("by_type") or {}
    if isinstance(by_type, dict):
        lines.append(
            "# HELP agent_task_outcomes_by_type_24h Task outcomes in 24h by task_type label.",
        )
        lines.append("# TYPE agent_task_outcomes_by_type_24h gauge")
        for task_type, bucket in by_type.items():
            if not isinstance(bucket, dict):
                continue
            tt = _label(str(task_type))
            for status in ("success", "failed"):
                n = int(bucket.get(status) or 0)
                if n:
                    lines.append(
                        f'agent_task_outcomes_by_type_24h{{task_type="{tt}",status="{status}"}} {n}'
                    )

    lines += [
        "# HELP agent_activity_samples_1h Behavior DB activity_samples rows in last 1h.",
        "# TYPE agent_activity_samples_1h gauge",
        f"agent_activity_samples_1h {int(data.get('activity_samples_1h') or 0)}",
        "# HELP agent_task_outcome_events_1h Task outcome rows inserted in last 1h.",
        "# TYPE agent_task_outcome_events_1h gauge",
        f"agent_task_outcome_events_1h {int(data.get('task_outcome_events_1h') or 0)}",
    ]
    return lines


@router.get("/prometheus")
def prometheus_metrics() -> Response:
    snap = telemetry_export_snapshot()
    body = "\n".join(_prometheus_lines(snap)) + "\n"
    return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")


@router.get("/snapshot")
def telegraf_snapshot_json() -> dict[str, Any]:
    """Optional JSON scrape (Telegraf inputs.http + json_v2); same data as Prometheus builder."""
    if not _enabled():
        return {"ok": False, "disabled": True}
    return {"ok": True, **telemetry_export_snapshot()}
