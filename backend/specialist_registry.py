"""Specialist role registry for BKLT Blacklight.

Inspired by agent roster libraries such as msitarzewski/agency-agents, but kept
small and local-first. Specialists are not separate models; they are routing
identities that tell the orchestrator which lens, deliverables, and checks to use.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Literal, TypedDict

SpecialistDomain = Literal[
    "engineering",
    "testing",
    "operations",
    "design",
    "product",
    "automation",
    "research",
    "memory",
]


class Specialist(TypedDict):
    id: str
    domain: SpecialistDomain
    title: str
    mission: str
    when_to_use: list[str]
    deliverables: list[str]
    capability_ids: list[str]


SPECIALISTS: dict[str, Specialist] = {
    "engineering.backend_architect": {
        "id": "engineering.backend_architect",
        "domain": "engineering",
        "title": "后端架构师",
        "mission": "审查 FastAPI、SQLite、工具调用、LLM 网关和模块边界，给出可维护的后端改造方案。",
        "when_to_use": ["后端", "接口", "数据库", "FastAPI", "工具调用", "架构", "模块"],
        "deliverables": ["接口设计", "数据模型", "风险点", "迁移步骤", "测试建议"],
        "capability_ids": ["project.health_check", "project.self_repair_plan", "integration.external_service"],
    },
    "engineering.frontend_developer": {
        "id": "engineering.frontend_developer",
        "domain": "engineering",
        "title": "前端工程师",
        "mission": "负责 React/Electron 界面、状态展示、可视化工作台和移动端入口的落地。",
        "when_to_use": ["前端", "React", "Electron", "界面", "UI", "可视化", "面板", "移动端"],
        "deliverables": ["组件结构", "交互状态", "接口字段", "构建检查", "可视化方案"],
        "capability_ids": ["project.health_check", "automation.flow"],
    },
    "testing.reality_checker": {
        "id": "testing.reality_checker",
        "domain": "testing",
        "title": "现实验收官",
        "mission": "只相信真实命令、真实日志和真实结果，避免假装完成。",
        "when_to_use": ["验证", "测试", "构建", "证据", "验收", "是否成功", "可行不可行"],
        "deliverables": ["已运行命令", "通过/失败证据", "阻塞项", "下一步最小验证"],
        "capability_ids": ["project.health_check", "project.self_repair_plan"],
    },
    "operations.sre": {
        "id": "operations.sre",
        "domain": "operations",
        "title": "本地 SRE",
        "mission": "处理启动、端口、进程、日志、模型网关、健康检查和恢复路径。",
        "when_to_use": ["启动不了", "端口", "日志", "health", "网关", "vLLM", "模型", "恢复", "监控"],
        "deliverables": ["现象", "假设", "检查命令", "止损方案", "恢复步骤"],
        "capability_ids": ["project.health_check", "desktop.app_control", "integration.external_service"],
    },
    "automation.flow_designer": {
        "id": "automation.flow_designer",
        "domain": "automation",
        "title": "自动化流程设计师",
        "mission": "把重复任务转成触发器、条件、动作、重试、确认和记录组成的自动化流程。",
        "when_to_use": ["自动化", "流程", "定时", "触发", "每天", "重复", "工作流", "提醒"],
        "deliverables": ["触发器", "条件", "动作列表", "重试策略", "确认点", "运行日志字段"],
        "capability_ids": ["automation.flow", "memory.remember_preference", "skill.self_evolve"],
    },
    "memory.habit_coach": {
        "id": "memory.habit_coach",
        "domain": "memory",
        "title": "习惯画像分析师",
        "mission": "分析用户长期偏好、工作习惯和上下文变化，产出可写入技能的建议。",
        "when_to_use": ["习惯", "偏好", "记住", "最近", "画像", "越来越懂", "个人", "长期"],
        "deliverables": ["行为模式", "偏好规则", "技能改写建议", "隐私边界", "回滚建议"],
        "capability_ids": ["memory.remember_preference", "skill.self_evolve"],
    },
    "research.agent_architect": {
        "id": "research.agent_architect",
        "domain": "research",
        "title": "Agent 架构研究员",
        "mission": "把外部 Agent/MCP/自动化项目的架构模式转成黑光可落地改造。",
        "when_to_use": ["深挖", "GitHub", "agent", "MCP", "框架", "Hermes", "LangGraph", "OpenHands"],
        "deliverables": ["可借鉴点", "不适合照搬的点", "黑光改造模块", "优先级", "风险"],
        "capability_ids": ["browser.web_task", "project.self_repair_plan", "skill.self_evolve"],
    },
    "design.control_plane_designer": {
        "id": "design.control_plane_designer",
        "domain": "design",
        "title": "控制台体验设计师",
        "mission": "把执行路线、工具轨迹、失败点、学习结果做成用户能看懂的黑光可视化体验。",
        "when_to_use": ["驾驶舱", "可视化", "视觉化", "时间线", "控制台", "面板", "体验"],
        "deliverables": ["页面信息架构", "状态流", "卡片字段", "交互动作", "空状态/失败态"],
        "capability_ids": ["automation.flow", "skill.self_evolve", "project.health_check"],
    },
}


def list_specialists() -> list[Specialist]:
    return [deepcopy(SPECIALISTS[key]) for key in sorted(SPECIALISTS)]


def get_specialist(specialist_id: str) -> Specialist:
    if specialist_id not in SPECIALISTS:
        raise KeyError(f"Unknown specialist: {specialist_id}")
    return deepcopy(SPECIALISTS[specialist_id])


def route_specialists(message: str, *, max_matches: int = 3) -> list[dict[str, object]]:
    text = (message or "").strip().lower()
    matches: list[dict[str, object]] = []
    for specialist in list_specialists():
        hits: list[str] = []
        for term in specialist["when_to_use"]:
            if term.lower() in text:
                hits.append(term)
        if hits:
            score = min(1.0, 0.35 + len(hits) * 0.22)
            matches.append({"specialist": specialist, "score": round(score, 3), "matched_terms": hits[:8]})
    matches.sort(key=lambda item: (item["score"], item["specialist"]["id"]), reverse=True)
    return matches[: max(1, int(max_matches or 3))]


def validate_specialists(known_capabilities: set[str] | None = None) -> list[str]:
    problems: list[str] = []
    for specialist_id, specialist in SPECIALISTS.items():
        if specialist["id"] != specialist_id:
            problems.append(f"{specialist_id} has mismatched id {specialist['id']}")
        if not specialist.get("when_to_use"):
            problems.append(f"{specialist_id} has no routing terms")
        if not specialist.get("deliverables"):
            problems.append(f"{specialist_id} has no deliverables")
        if known_capabilities is not None:
            for capability_id in specialist.get("capability_ids", []):
                if capability_id not in known_capabilities:
                    problems.append(f"{specialist_id} references unknown capability: {capability_id}")
    return problems
