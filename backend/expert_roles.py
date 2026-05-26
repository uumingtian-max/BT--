"""超级智能体·十一专家 + 大佬（用户）。默认顶级模式开启。"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXPERT_ROLES_MD = _REPO_ROOT / "meta" / "expert-roles.md"
_ROLES_SKILL = _REPO_ROOT / ".cursor" / "skills" / "super-agent-eleven" / "references" / "roles.md"

ExpertId = Literal[
    "boss",
    "architect",
    "fullstack",
    "ux",
    "multimodal",
    "performance",
    "brand_3d_visual",
    "security",
    "qa",
    "orchestrator",
    "avatar_3d",
    "visual_luxury",
]

# 顶级模式：固定拉起 #1–#11（不含大佬 #0）
ELEVEN_EXPERT_PIPELINE: tuple[str, ...] = (
    "architect",
    "fullstack",
    "ux",
    "multimodal",
    "performance",
    "brand_3d_visual",
    "security",
    "qa",
    "orchestrator",
    "avatar_3d",
    "visual_luxury",
)

EXPERT_INDEX: list[dict[str, Any]] = [
    {"id": "boss", "no": 0, "name": "大佬", "lead": True, "keywords": []},
    {"id": "architect", "no": 1, "name": "超级架构师·Pro", "keywords": ["架构", "规划", "任务链", "拆解", "30步", "断点"]},
    {"id": "fullstack", "no": 2, "name": "全栈工程师·顶级", "keywords": ["代码", "实现", "部署", "api", "工具"]},
    {"id": "ux", "no": 3, "name": "交互体验专家·超拟人", "keywords": ["对话", "记忆", "意图", "体验"]},
    {"id": "multimodal", "no": 4, "name": "多模态专家·全模态", "keywords": ["图片", "视频", "语音", "3d", "文件"]},
    {"id": "performance", "no": 5, "name": "系统优化专家·极限", "keywords": ["性能", "并发", "卡顿", "优化", "容错"]},
    {"id": "brand_3d_visual", "no": 6, "name": "品牌+3D+视觉", "keywords": ["界面", "ui", "奢品", "3d", "品牌"]},
    {"id": "security", "no": 7, "name": "安全合规专家·企业级", "keywords": ["安全", "合规", "隐私", "审计"]},
    {"id": "qa", "no": 8, "name": "测试验收专家·全维度", "keywords": ["测试", "验收", "qa", "回归"]},
    {"id": "orchestrator", "no": 9, "name": "总控编排·Orchestrator", "keywords": ["编排", "并行", "总控"]},
    {"id": "avatar_3d", "no": 10, "name": "3D形象大师·超写实", "keywords": ["捏脸", "表情", "骨骼", "形变"]},
    {"id": "visual_luxury", "no": 11, "name": "视觉美学总监·奢品级", "keywords": ["排版", "动效", "配色", "爱马仕"]},
]


def _env_flag(name: str, default: str = "1") -> bool:
    raw = (os.getenv(name) or default).strip().lower()
    return raw not in ("0", "false", "off", "no")


def is_super_agent_enabled() -> bool:
    """顶级十一专家模式：默认开启，显式 BKLT_SUPER_AGENT=0 才关闭。"""
    if not _env_flag("BKLT_SUPER_AGENT", "1") or not _env_flag("SUPER_AGENT_ELEVEN", "1"):
        return False
    tier = (os.getenv("AGENT_TIER") or os.getenv("BKLT_AGENT_TIER") or "super").strip().lower()
    if tier in ("standard", "basic", "default") and not _env_flag("BKLT_SUPER_AGENT", "1"):
        return False
    return True


def is_boss_mode() -> bool:
    if not is_super_agent_enabled():
        return False
    return _env_flag("BKLT_BOSS_MODE", "1")


def super_agent_max_steps(default: int) -> int:
    if not is_super_agent_enabled():
        return default
    cap = max(6, min(30, int(os.getenv("BKLT_SUPER_AGENT_MAX_STEPS", "24") or "24")))
    return max(default, cap)


def eleven_expert_ids_for_task(message: str) -> list[str]:
    """顶级：固定十一席流水线；可按关键词把 #10/#11 提前，但十一席都会执行。"""
    text = (message or "").lower()
    order = list(ELEVEN_EXPERT_PIPELINE)
    if any(k in text for k in ("3d", "捏脸", "表情", "avatar")):
        for eid in ("avatar_3d", "brand_3d_visual"):
            if eid in order:
                order.remove(eid)
                order.insert(2, eid)
    if any(k in text for k in ("ui", "界面", "视觉", "奢品", "排版")):
        if "visual_luxury" in order:
            order.remove("visual_luxury")
            order.insert(3, "visual_luxury")
    return order


def _read_expert_roles_markdown() -> str:
    for path in (_EXPERT_ROLES_MD, _ROLES_SKILL):
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    return ""


def route_experts(message: str, *, limit: int = 12) -> list[dict[str, Any]]:
    """返回大佬 + 当前任务相关的十一专家席位（manifest 用）。"""
    ids = eleven_expert_ids_for_task(message)
    experts = [next(x for x in EXPERT_INDEX if x["id"] == eid) for eid in ids]
    return [{"id": "boss", "no": 0, "name": "大佬", "role": "decision_maker"}] + [
        {**row, "role": "pipeline", "order": i + 1} for i, row in enumerate(experts[: limit - 1])
    ]


def build_super_agent_system_addendum() -> str:
    if not is_super_agent_enabled():
        return ""
    lines = [
        "## 超级智能体·顶级十一专家（已启用）",
        "- **#0 大佬=用户**：你发言结束 → **只收最终结果**，不要过程、不要分工表、不要「请说下一步」。",
        "- **#1–#11**：后台自动全员协作，用户**不用管**专家；你只对外交付成品。",
        "- 内部：≤30步任务链、动态工具、断点续跑、安全(#7)+验收(#8)闸门。",
        "- 对标：**智商超 Opus + 执行超 Manus**。",
        "- 默认：直接选工具执行（`run_shell`/`read_file`/`web_search` 等），#1 在内部规划，不对大佬展开过程。",
        "- 仅当用户明确要求「编排/多模型/方案对比/总控」时才 `run_task_orchestration`（执行内核：#1 第一席，≤4 次 LLM）。",
    ]
    if is_boss_mode():
        lines.append("- **大佬模式**：禁止过程句；仅 `final_answer` / 必要 `tool_result` / `error`。")
    return "\n".join(lines)


def get_expert_roles_manifest() -> dict[str, Any]:
    md = _read_expert_roles_markdown()
    beyond_manus = re.findall(r"^### \d+\. .+$", md, flags=re.MULTILINE) if md else []
    return {
        "ok": True,
        "mode": "super_agent_eleven_top",
        "enabled": is_super_agent_enabled(),
        "boss_mode": is_boss_mode(),
        "positioning": "智商超 Opus + 执行超 Manus",
        "pipeline": list(ELEVEN_EXPERT_PIPELINE),
        "experts": EXPERT_INDEX,
        "beyond_manus_checks": beyond_manus
        or [
            "执行能力",
            "复杂流程",
            "工具调用",
            "交互体验",
            "形态+界面",
            "智商层面",
        ],
        "docs": {
            "expert_roles_md": str(_EXPERT_ROLES_MD),
            "roles_reference": str(_ROLES_SKILL),
        },
        "env": {
            "BKLT_SUPER_AGENT": os.getenv("BKLT_SUPER_AGENT", "1"),
            "BKLT_BOSS_MODE": os.getenv("BKLT_BOSS_MODE", "1"),
            "BKLT_SUPER_AGENT_MAX_STEPS": os.getenv("BKLT_SUPER_AGENT_MAX_STEPS", "24"),
            "AGENT_TIER": os.getenv("AGENT_TIER", "super"),
        },
    }


def should_emit_process_step(step_type: str) -> bool:
    if not is_boss_mode():
        return True
    return step_type in ("final_answer", "tool_result", "error")


def apply_super_agent_defaults() -> None:
    """启动时注入默认顶级配置（可被 .env 覆盖）。"""
    defaults = {
        "BKLT_SUPER_AGENT": "1",
        "BKLT_BOSS_MODE": "1",
        "BKLT_SUPER_AGENT_MAX_STEPS": "24",
        "AGENT_TIER": "super",
        "AGENT_SKILL_PACK": os.getenv("AGENT_SKILL_PACK", "1"),
    }
    for key, val in defaults.items():
        if not (os.getenv(key) or "").strip():
            os.environ[key] = val
