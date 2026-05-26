"""专家编排入口：默认走执行内核，不再 11 路连聊。"""

from __future__ import annotations

from orchestrator import ModelProfile


def build_expert_subtasks(
    message: str,
    profile: ModelProfile,
    evolution_context: str = "",
) -> list[dict[str, str]]:
    from execution_kernel import build_kernel_subtasks, is_execution_kernel_enabled

    if is_execution_kernel_enabled():
        return build_kernel_subtasks(message, profile, evolution_context)
    return []
