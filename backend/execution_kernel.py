"""执行内核：编排走 #1 架构师牵头 + ≤4 席 LLM，替代默认多路连聊。"""

from __future__ import annotations

import os
from typing import Any

from agent_runtime import get_runtime
from context_pack import compress_for_llm
from orchestrator import ModelProfile
from workflow_store import build_workflow_context


def _env_flag(name: str, default: str = "1") -> bool:
    raw = (os.getenv(name) or default).strip().lower()
    return raw not in ("0", "false", "off", "no")


def is_execution_kernel_enabled() -> bool:
    return _env_flag("EXECUTION_KERNEL", "1")


def apply_execution_kernel_defaults() -> None:
    defaults = {
        "EXECUTION_KERNEL": "1",
        "BKLT_SUPER_AGENT": "1",
        "BKLT_BOSS_MODE": "1",
    }
    for key, val in defaults.items():
        if not (os.getenv(key) or "").strip():
            os.environ[key] = val
    try:
        from expert_roles import apply_super_agent_defaults

        apply_super_agent_defaults()
    except Exception:
        pass


def build_kernel_subtasks(
    message: str,
    profile: ModelProfile,
    evolution_context: str = "",
) -> list[dict[str, str]]:
    rt = get_runtime()
    workflow_context = compress_for_llm(
        build_workflow_context(message), rt.context_block_max_chars, "workflow"
    )
    base_ctx = f"{evolution_context}\n\n{workflow_context}\n\n任务：{message}"
    text = message.lower()
    subs: list[dict[str, str]] = [
        {
            "kind": "expert_architect",
            "title": "#1 超级架构师·Pro",
            "model_name": profile.planner_model,
            "prompt": (
                "你是【#1 超级架构师·Pro】。只输出：≤12 步可执行任务链（编号）、依赖、断点、建议工具序列。\n"
                "禁止空话与分工表。\n" + base_ctx
            ),
        },
        {
            "kind": "expert_fullstack",
            "title": "#2 全栈工程师·顶级",
            "model_name": profile.coder_model,
            "prompt": (
                "你是【#2 全栈】。给出可直接落地的实现要点（路径/命令/配置），不超过 8 条。\n"
                + base_ctx
            ),
        },
    ]
    if any(k in text for k in ("安全", "合规", "隐私", "密钥", "token", "密码", "审计")):
        subs.append(
            {
                "kind": "expert_security",
                "title": "#7 安全合规",
                "model_name": profile.reviewer_model,
                "prompt": "你是【#7 安全合规】。列出 3 条风险与必须闸门。\n" + base_ctx,
            }
        )
    if any(k in text for k in ("图", "视频", "语音", "附件", "屏幕", "3d", "多模态")):
        vision = profile.vision_model or profile.planner_model
        subs.append(
            {
                "kind": "expert_multimodal",
                "title": "#4 多模态",
                "model_name": vision,
                "prompt": "你是【#4 多模态】。说明本任务需要的模态工具链（一段）。\n" + base_ctx,
            }
        )
    try:
        from expert_roles import is_monetize_experts_enabled, pick_monetize_kernel_subtask

        if is_monetize_experts_enabled():
            mon = pick_monetize_kernel_subtask(message)
            if mon:
                subs.insert(
                    2,
                    {
                        **mon,
                        "model_name": profile.planner_model,
                        "prompt": mon["prompt"] + base_ctx,
                    },
                )
    except Exception:
        pass
    subs.append(
        {
            "kind": "expert_qa",
            "title": "#8 测试验收",
            "model_name": profile.reviewer_model,
            "prompt": (
                "你是【#8 测试验收】。输出：验收清单 3-5 条 + 最可能失败点 2 条。\n" + base_ctx
            ),
        }
    )
    return subs[:4]


def kernel_synthesis_instructions() -> str:
    return (
        "你是黑光总控（大佬模式）。后台已走执行内核：#1 超级架构师已出任务链，其余席为要点片段。\n"
        "要求：\n"
        "1. 直接给结论与可执行下一步（3-6 条），不要复述专家名、不要分工表\n"
        "2. 不要解释如何调用模型\n"
        "3. 中文，可执行"
    )


def execution_kernel_status() -> dict[str, Any]:
    try:
        from expert_roles import get_expert_roles_manifest, is_super_agent_enabled

        super_on = is_super_agent_enabled()
        manifest = get_expert_roles_manifest()
        counts = manifest.get("counts") or {}
    except Exception:
        super_on = False
        counts = {}
    return {
        "ok": True,
        "execution_kernel": is_execution_kernel_enabled(),
        "super_agent_eleven": super_on,
        "monetize_27": counts.get("monetize_experts", 27),
        "total_expert_roles": counts.get("total_roles", 39),
        "orchestration_mode": "execution_kernel" if is_execution_kernel_enabled() else "legacy",
        "first_seat": "#1 超级架构师·Pro",
        "max_llm_seats": 4,
    }
