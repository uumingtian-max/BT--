"""Adaptive task planning — atomic steps with optional self-correction."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from agent_runtime import get_runtime
from llm_client import chat_complete_async

ToolExecutor = Callable[[str, dict[str, Any]], str]

_MULTI_STEP_MARKERS = (
    "分步",
    "步骤",
    "先",
    "然后",
    "接着",
    "最后",
    "第一步",
    "第二步",
    "多步",
    "流水线",
    "workflow",
    "pipeline",
)


class AdaptiveDispatcher:
    """Intent plan → sequential tool steps → refine after each observation."""

    async def generate_plan(self, user_input: str) -> list[dict[str, Any]]:
        text = (user_input or "").strip()
        if not text:
            return []
        if not any(m in text.lower() for m in _MULTI_STEP_MARKERS) and len(text) < 80:
            return [{"step": 1, "tool": "auto", "goal": text}]

        rt = get_runtime()
        messages = [
            {
                "role": "system",
                "content": (
                    "将用户任务拆成 2-5 个原子步骤 JSON 数组。"
                    '每项: {"step":n,"tool":"search|read|write|code|browser|orchestrate|auto","goal":"..."}。'
                    "只输出 JSON 数组，不要 markdown。"
                ),
            },
            {"role": "user", "content": text[:3000]},
        ]
        try:
            raw = await chat_complete_async(messages, rt.reasoning_model, temperature=0.1)
            m = re.search(r"\[[\s\S]*\]", raw)
            if m:
                plan = json.loads(m.group(0))
                if isinstance(plan, list) and plan:
                    return plan[:8]
        except Exception:
            pass
        return [
            {"step": 1, "tool": "search", "goal": text},
            {"step": 2, "tool": "auto", "goal": f"汇总并完成：{text[:200]}"},
        ]

    async def refine_plan(
        self, plan: list[dict[str, Any]], last_result: str, current_index: int
    ) -> list[dict[str, Any]]:
        if current_index >= len(plan) - 1:
            return plan
        preview = (last_result or "")[:1500]
        if "error" not in preview.lower() and "失败" not in preview:
            return plan
        rt = get_runtime()
        messages = [
            {
                "role": "system",
                "content": "上一步失败。输出修订后的剩余步骤 JSON 数组（从下一步开始），只输出 JSON。",
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"failed_step": plan[current_index], "error_preview": preview},
                    ensure_ascii=False,
                ),
            },
        ]
        try:
            raw = await chat_complete_async(messages, rt.fast_model, temperature=0.1)
            m = re.search(r"\[[\s\S]*\]", raw)
            if m:
                tail = json.loads(m.group(0))
                if isinstance(tail, list) and tail:
                    return plan[:current_index] + tail[:6]
        except Exception:
            pass
        return plan

    def _map_tool(self, step: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        tool = str(step.get("tool") or "auto").lower()
        goal = str(step.get("goal") or "").strip()
        if tool == "search":
            return "web_search", {"query": goal}
        if tool == "read":
            return "list_files", {"directory": "~/Desktop"}
        if tool == "write":
            return "list_files", {"directory": str(get_runtime().agent_file_root or ".")}
        if tool == "code":
            return "execute_python", {"code": goal[:8000]}
        if tool == "browser":
            return "browser_navigate", {
                "url": goal if goal.startswith("http") else f"https://www.google.com/search?q={goal}"
            }
        if tool == "orchestrate":
            return "run_task_orchestration", {"message": goal}
        return "local_search", {"query": goal}

    async def dispatch(
        self,
        user_input: str,
        executor: ToolExecutor,
        *,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        from visual_event_bus import publish_event

        plan = await self.generate_plan(user_input)
        results: list[dict[str, Any]] = []
        publish_event(
            event_type="plan_created",
            source="adaptive_dispatch",
            title=f"计划 {len(plan)} 步",
            payload={"plan": plan},
            run_id=run_id,
            status="info",
        )
        for i, task in enumerate(plan):
            tool_name, params = self._map_tool(task)
            publish_event(
                event_type="neural_pulse",
                source="adaptive_dispatch",
                title=f"步骤 {task.get('step', i + 1)} → {tool_name}",
                payload={"task": task, "tool": tool_name},
                run_id=run_id,
                status="active",
            )
            try:
                output = executor(tool_name, params)
            except Exception as exc:
                output = f"error: {exc}"
            results.append({"task": task, "tool": tool_name, "output": output[:4000]})
            plan = await self.refine_plan(plan, output, i)
        return {"ok": True, "plan": plan, "results": results, "summary": self.synthesize_final_response(results)}

    @staticmethod
    def synthesize_final_response(results: list[dict[str, Any]]) -> str:
        if not results:
            return "未执行任何步骤。"
        lines = ["## 自适应执行摘要"]
        for i, row in enumerate(results, 1):
            goal = (row.get("task") or {}).get("goal", "")
            tool = row.get("tool", "")
            preview = str(row.get("output", ""))[:500]
            lines.append(f"### 步骤 {i} ({tool})\n{goal}\n\n{preview}")
        return "\n\n".join(lines)
