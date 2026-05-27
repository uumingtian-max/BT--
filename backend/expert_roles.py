"""超级智能体·核心十一专家 + 变现自动化二十七专家 + 大佬。"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from expert_monetize_27 import MONETIZE_27, MONETIZE_IDS

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXPERT_ROLES_MD = _REPO_ROOT / "meta" / "expert-roles.md"
_MONETIZE_MD = _REPO_ROOT / "meta" / "expert-roles-monetize-27.md"
_ROLES_SKILL = _REPO_ROOT / ".cursor" / "skills" / "super-agent-eleven" / "references" / "roles.md"

ExpertId = str

# 核心流水线 #1–#11（不含大佬 #0）
CORE_EXPERT_PIPELINE: tuple[str, ...] = (
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
# 兼容旧名
ELEVEN_EXPERT_PIPELINE = CORE_EXPERT_PIPELINE

_CORE_INDEX: list[dict[str, Any]] = [
    {"id": "boss", "no": 0, "name": "大佬", "lead": True, "tier": "core", "keywords": []},
    {"id": "architect", "no": 1, "name": "超级架构师·Pro", "tier": "core", "keywords": ["架构", "规划", "任务链", "拆解", "30步", "断点"]},
    {"id": "fullstack", "no": 2, "name": "全栈工程师·顶级", "tier": "core", "keywords": ["代码", "实现", "部署", "api", "工具"]},
    {"id": "ux", "no": 3, "name": "交互体验专家·超拟人", "tier": "core", "keywords": ["对话", "记忆", "意图", "体验"]},
    {"id": "multimodal", "no": 4, "name": "多模态专家·全模态", "tier": "core", "keywords": ["图片", "视频", "语音", "3d", "文件"]},
    {"id": "performance", "no": 5, "name": "系统优化专家·极限", "tier": "core", "keywords": ["性能", "并发", "卡顿", "优化", "容错"]},
    {"id": "brand_3d_visual", "no": 6, "name": "品牌+3D+视觉", "tier": "core", "keywords": ["界面", "ui", "奢品", "3d", "品牌"]},
    {"id": "security", "no": 7, "name": "安全合规专家·企业级", "tier": "core", "keywords": ["安全", "合规", "隐私", "审计"]},
    {"id": "qa", "no": 8, "name": "测试验收专家·全维度", "tier": "core", "keywords": ["测试", "验收", "qa", "回归"]},
    {"id": "orchestrator", "no": 9, "name": "总控编排·Orchestrator", "tier": "core", "keywords": ["编排", "并行", "总控"]},
    {"id": "avatar_3d", "no": 10, "name": "3D形象大师·超写实", "tier": "core", "keywords": ["捏脸", "表情", "骨骼", "形变"]},
    {"id": "visual_luxury", "no": 11, "name": "视觉美学总监·奢品级", "tier": "core", "keywords": ["排版", "动效", "配色", "爱马仕"]},
]

_MONETIZE_INDEX: list[dict[str, Any]] = [
    {**row, "tier": "monetize", "lead": False} for row in MONETIZE_27
]

EXPERT_INDEX: list[dict[str, Any]] = _CORE_INDEX + _MONETIZE_INDEX

_EXPERT_BY_ID: dict[str, dict[str, Any]] = {x["id"]: x for x in EXPERT_INDEX}


def _env_flag(name: str, default: str = "1") -> bool:
    raw = (os.getenv(name) or default).strip().lower()
    return raw not in ("0", "false", "off", "no")


def is_monetize_experts_enabled() -> bool:
    return _env_flag("BKLT_MONETIZE_27", "1")


def is_super_agent_enabled() -> bool:
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


def _score_expert(text: str, keywords: list[str]) -> int:
    low = text.lower()
    score = 0
    for kw in keywords:
        k = kw.lower()
        if k and k in low:
            score += 2 if len(k) >= 4 else 1
    return score


def monetize_expert_ids_for_task(message: str, *, limit: int | None = None) -> list[str]:
    """按关键词匹配 #12–#38，默认最多 3 席（可 env 调）。"""
    if not is_monetize_experts_enabled():
        return []
    cap = limit
    if cap is None:
        cap = max(1, min(5, int(os.getenv("BKLT_MONETIZE_ROUTE_MAX", "3") or "3")))
    text = (message or "").lower()
    scored: list[tuple[int, int, str]] = []
    for row in MONETIZE_27:
        s = _score_expert(text, list(row.get("keywords") or []))
        if s > 0:
            scored.append((s, int(row["no"]), row["id"]))
    scored.sort(key=lambda x: (-x[0], x[1]))
    if not scored and any(k in text for k in ("赚钱", "变现", "收入", "自动化", "money", "revenue")):
        return ["revenue_architect", "workflow_automation", "passive_income_audit"][:cap]
    return [eid for _, _, eid in scored[:cap]]


def eleven_expert_ids_for_task(message: str) -> list[str]:
    text = (message or "").lower()
    order = list(CORE_EXPERT_PIPELINE)
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


def experts_for_task(message: str) -> list[str]:
    """核心流水线 + 匹配的变现专家（manifest / UI 用）。"""
    core = eleven_expert_ids_for_task(message)
    monetize = monetize_expert_ids_for_task(message)
    seen: set[str] = set()
    out: list[str] = []
    for eid in core + monetize:
        if eid not in seen:
            seen.add(eid)
            out.append(eid)
    return out


def get_expert_by_id(expert_id: str) -> dict[str, Any] | None:
    return _EXPERT_BY_ID.get(expert_id)


def pick_monetize_kernel_subtask(message: str) -> dict[str, str] | None:
    """执行内核可选加 1 席变现专家（仍受 execution_kernel 总席位数限制）。"""
    ids = monetize_expert_ids_for_task(message, limit=1)
    if not ids:
        return None
    row = _EXPERT_BY_ID.get(ids[0])
    if not row:
        return None
    focus = row.get("focus") or row["name"]
    return {
        "kind": f"expert_{row['id']}",
        "title": f"#{row['no']} {row['name']}",
        "prompt": (
            f"你是【#{row['no']} {row['name']}】。职责：{focus}。\n"
            "只输出：可执行步骤 3-6 条 + 关键指标 2 个 + 风险 1 条。禁止空话。\n"
        ),
    }


def _read_expert_roles_markdown() -> str:
    parts: list[str] = []
    for path in (_EXPERT_ROLES_MD, _MONETIZE_MD, _ROLES_SKILL):
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(parts)


def route_experts(message: str, *, limit: int = 40) -> list[dict[str, Any]]:
    ids = experts_for_task(message)
    experts = [_EXPERT_BY_ID[eid] for eid in ids if eid in _EXPERT_BY_ID]
    return [{"id": "boss", "no": 0, "name": "大佬", "role": "decision_maker"}] + [
        {**row, "role": "pipeline" if row.get("tier") == "core" else "monetize", "order": i + 1}
        for i, row in enumerate(experts[: limit - 1])
    ]


def build_super_agent_system_addendum() -> str:
    if not is_super_agent_enabled():
        return ""
    lines = [
        "## 超级智能体·核心十一专家 + 变现二十七专家（已启用）",
        "- **#0 大佬=用户**：只收最终结果，不要过程、不要分工表。",
        "- **#1–#11 核心席**：工程/体验/安全/验收；默认直接调工具执行。",
        "- **#12–#38 变现席**：自动化、获客、转化、合规与现金流；按任务关键词**只激活相关 1–3 席**，不全员连聊。",
        "- 执行内核：≤4 次 LLM（#1 架构牵头 + 全栈 + 验收 + 可选安全/多模态/变现席）。",
        "- 对标：**能落地的赚钱自动化**，不是空谈商业计划。",
        "- 涉及投资/医疗/法律承诺时：#30 合规闸门优先，不给违规捷径。",
    ]
    if is_boss_mode():
        lines.append("- **大佬模式**：禁止过程句；仅 `final_answer` / 必要 `tool_result` / `error`。")
    return "\n".join(lines)


def get_expert_roles_manifest() -> dict[str, Any]:
    md = _read_expert_roles_markdown()
    beyond_manus = re.findall(r"^### \d+\. .+$", md, flags=re.MULTILINE) if md else []
    return {
        "ok": True,
        "mode": "super_agent_core_11_plus_monetize_27",
        "enabled": is_super_agent_enabled(),
        "monetize_27_enabled": is_monetize_experts_enabled(),
        "boss_mode": is_boss_mode(),
        "positioning": "智商超 Opus + 执行超 Manus + 变现自动化二十七席",
        "counts": {
            "total_roles": len(EXPERT_INDEX),
            "core_experts": len(CORE_EXPERT_PIPELINE),
            "monetize_experts": len(MONETIZE_27),
            "with_boss": len(EXPERT_INDEX),
        },
        "pipeline_core": list(CORE_EXPERT_PIPELINE),
        "pipeline_monetize_ids": list(MONETIZE_IDS),
        "experts": EXPERT_INDEX,
        "beyond_manus_checks": beyond_manus
        or [
            "执行能力",
            "复杂流程",
            "工具调用",
            "交互体验",
            "形态+界面",
            "智商层面",
            "变现自动化",
        ],
        "docs": {
            "expert_roles_md": str(_EXPERT_ROLES_MD),
            "expert_monetize_md": str(_MONETIZE_MD),
            "roles_reference": str(_ROLES_SKILL),
        },
        "env": {
            "BKLT_SUPER_AGENT": os.getenv("BKLT_SUPER_AGENT", "1"),
            "BKLT_MONETIZE_27": os.getenv("BKLT_MONETIZE_27", "1"),
            "BKLT_MONETIZE_ROUTE_MAX": os.getenv("BKLT_MONETIZE_ROUTE_MAX", "3"),
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
    defaults = {
        "BKLT_SUPER_AGENT": "1",
        "BKLT_MONETIZE_27": "1",
        "BKLT_MONETIZE_ROUTE_MAX": "3",
        "BKLT_BOSS_MODE": "1",
        "BKLT_SUPER_AGENT_MAX_STEPS": "24",
        "AGENT_TIER": "super",
        "AGENT_SKILL_PACK": os.getenv("AGENT_SKILL_PACK", "1"),
    }
    for key, val in defaults.items():
        if not (os.getenv(key) or "").strip():
            os.environ[key] = val
