"""Run multiple LLM sub-prompts in parallel (Hermes-style delegation lite)."""

from __future__ import annotations

import asyncio

from agent_runtime import get_runtime
from llm_client import chat_complete_async


async def run_parallel_subagents(
    tasks: list[str],
    *,
    model: str | None = None,
    max_tasks: int = 5,
) -> str:
    rt = get_runtime()
    m = (model or "").strip() or rt.default_chat_model
    items = [str(t).strip() for t in tasks if str(t).strip()][:max_tasks]
    if not items:
        return "run_parallel_subagents error: 需要 tasks 字符串数组或非空多行文本"

    async def one(i: int, prompt: str) -> tuple[int, str]:
        try:
            text = await chat_complete_async(
                [{"role": "user", "content": prompt}],
                m,
                temperature=0.2,
            )
            return i, (text or "").strip()
        except Exception as e:
            return i, f"[子任务 {i + 1} 失败] {e}"

    results = await asyncio.gather(*[one(i, p) for i, p in enumerate(items)])
    lines = []
    for i, text in sorted(results, key=lambda x: x[0]):
        lines.append(f"### 子任务 {i + 1}\n{text}\n")
    return "\n".join(lines)


def run_parallel_subagents_sync(tasks: list[str], model: str | None = None) -> str:
    return asyncio.run(run_parallel_subagents(tasks, model=model))
