"""Run graph instrumentation for /agent/run.

This module wraps ``agent.run_agent`` without rewriting the large Agent loop. It
persists the same streamed steps that the frontend already receives, so the
trace is low-risk and stays aligned with current SSE behavior.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from fastapi import HTTPException

from run_graph_store import add_run_step, finish_run_graph, get_run_graph, list_run_graphs, start_run_graph
from visual_event_bus import publish_event

_PATCHED = False
_ROUTES_ADDED = False


def _step_name(step: dict[str, Any]) -> str:
    step_type = str(step.get("type") or "step")
    if step.get("tool"):
        return f"{step_type}:{step.get('tool')}"
    return step_type


def _step_status(step: dict[str, Any]) -> str:
    step_type = str(step.get("type") or "")
    content = str(step.get("content") or step.get("result") or "")
    lowered = content.lower()
    if step_type in ("tool_confirm_required",):
        return "waiting_confirmation"
    if step_type == "final_answer" and "这次我没有真正把任务做完" in content:
        return "failed"
    if "tool error:" in lowered or lowered.startswith("error:"):
        return "failed"
    return "success"


def _step_output(step: dict[str, Any]) -> dict[str, Any]:
    step_type = str(step.get("type") or "step")
    output: dict[str, Any] = {"raw": step}
    if "content" in step:
        output["content"] = str(step.get("content") or "")[:8000]
    if "result" in step:
        output["result"] = str(step.get("result") or "")[:8000]
    if step_type == "tool_call":
        output["tool"] = step.get("tool")
        output["params"] = step.get("params") or {}
    if step_type == "tool_result":
        output["tool"] = step.get("tool")
    if step_type == "tool_confirm_required":
        output["tool"] = step.get("tool")
        output["risk_level"] = step.get("risk_level")
        output["params"] = step.get("params") or {}
    return output


def _add_agent_graph_routes(agent_module) -> None:
    global _ROUTES_ADDED
    if _ROUTES_ADDED:
        return

    def agent_graphs(limit: int = 50, status: str | None = None):
        return {"ok": True, "graphs": list_run_graphs(limit=limit, source="agent", status=status)}

    def agent_run_graph_detail(run_id: str):
        graph = get_run_graph(run_id)
        if not graph or graph.get("source") != "agent":
            raise HTTPException(404, "agent run graph not found")
        return {"ok": True, "graph": graph}

    agent_module.router.add_api_route("/graphs", agent_graphs, methods=["GET"], tags=["agent"])
    agent_module.router.add_api_route("/runs/{run_id}/graph", agent_run_graph_detail, methods=["GET"], tags=["agent"])
    _ROUTES_ADDED = True


def apply_agent_run_graph_patch() -> bool:
    """Patch agent.run_agent once. Returns True when patched by this call."""
    global _PATCHED

    import agent as agent_module

    _add_agent_graph_routes(agent_module)

    if _PATCHED:
        return False

    original_run_agent = agent_module.run_agent

    async def run_agent_with_graph(
        message: str,
        model: str,
        session_id: str | None = None,
        on_step: Callable[[dict[str, Any]], Awaitable[None] | None] | None = None,
    ):
        started = time.perf_counter()
        run = start_run_graph(
            source="agent",
            kind="agent_run",
            title=(message or "Agent run")[:120],
            target=session_id or "agent",
            metadata={"model": model, "session_id": session_id, "message_preview": (message or "")[:500]},
        )
        run_id = run["id"]
        publish_event(
            event_type="agent_run_started",
            source="agent",
            title="开始 Agent 任务",
            payload={"model": model, "session_id": session_id, "message_preview": (message or "")[:300]},
            run_id=run_id,
            status="running",
        )

        final_status = "success"
        final_summary = "Agent 任务完成"

        async def traced_on_step(step: dict[str, Any]):
            nonlocal final_status, final_summary
            status = _step_status(step)
            step_type = str(step.get("type") or "step")
            if status == "failed":
                final_status = "failed"
            if step_type == "final_answer":
                final_summary = str(step.get("content") or final_summary)[:300]
            add_run_step(
                run_id=run_id,
                step_type=step_type,
                name=_step_name(step),
                status=status,
                input_data={"message_preview": (message or "")[:500]} if step_type == "thinking" else {},
                output_data=_step_output(step),
            )
            publish_event(
                event_type=f"agent_{step_type}",
                source="agent",
                title=_step_name(step),
                payload=_step_output(step),
                run_id=run_id,
                status=status,
            )
            if on_step is None:
                return None
            maybe_awaitable = on_step(step)
            if hasattr(maybe_awaitable, "__await__"):
                await maybe_awaitable
            return None

        try:
            steps = await original_run_agent(message, model, session_id, traced_on_step)
            if not any(step.get("type") == "final_answer" for step in steps):
                final_status = "failed"
                final_summary = "Agent 任务未生成最终回答"
            return steps
        except Exception as exc:
            final_status = "failed"
            final_summary = f"Agent 任务异常：{exc}"
            add_run_step(
                run_id=run_id,
                step_type="error",
                name="agent_exception",
                status="failed",
                output_data={"error": str(exc)},
            )
            publish_event(
                event_type="agent_run_failed",
                source="agent",
                title=final_summary,
                payload={"error": str(exc)},
                run_id=run_id,
                status="failed",
            )
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            finish_run_graph(
                run_id,
                status=final_status,
                summary=final_summary,
                duration_ms=duration_ms,
                metadata={"model": model, "session_id": session_id, "message_preview": (message or "")[:500]},
            )
            publish_event(
                event_type="agent_run_finished",
                source="agent",
                title=final_summary,
                payload={"status": final_status, "duration_ms": duration_ms},
                run_id=run_id,
                status=final_status,
            )

    agent_module.run_agent = run_agent_with_graph
    _PATCHED = True
    return True
