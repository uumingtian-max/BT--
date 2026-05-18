"""Intent router for BKLT Blacklight capabilities.

This is the first lightweight layer between natural language and low-level tool
selection.  It does not execute tools.  It classifies a user utterance into
candidate capabilities and returns a transparent plan that the UI can show before
execution.
"""

from __future__ import annotations

import re
from typing import Any, TypedDict

from capability_registry import CapabilityMetadata, list_capabilities


class CapabilityMatch(TypedDict):
    capability: CapabilityMetadata
    score: float
    matched_terms: list[str]


class IntentRoute(TypedDict):
    user_text: str
    primary_intent: str
    confidence: float
    needs_confirmation: bool
    risk_level: str
    matches: list[CapabilityMatch]
    plan: list[dict[str, Any]]
    notes: list[str]


_RISK_WEIGHT = {"safe": 0, "confirm": 1, "dangerous": 2}

# Extra Chinese/English trigger words that are broader than the examples in the
# capability registry.  They keep the first version deterministic and explainable
# without needing another LLM call.
DOMAIN_HINTS: dict[str, list[str]] = {
    "system.eye_comfort": [
        "护眼",
        "夜间",
        "夜晚",
        "屏幕",
        "刺眼",
        "太亮",
        "调暗",
        "亮度",
        "蓝光",
        "深色",
        "dark mode",
        "night light",
    ],
    "desktop.app_control": [
        "窗口",
        "软件",
        "应用",
        "切换",
        "聚焦",
        "快捷键",
        "输入",
        "点击",
        "打开程序",
        "当前窗口",
    ],
    "browser.web_task": ["浏览器", "网页", "表单", "截图", "点击网页", "打开网址", "登录页"],
    "files.organize_workspace": ["桌面", "文件", "目录", "下载", "整理", "归类", "读取", "写报告"],
    "project.health_check": ["项目", "测试", "构建", "检查", "健康", "git", "github", "仓库", "黑光"],
    "project.self_repair_plan": ["修复", "报错", "bug", "优化", "维护", "自己改", "自己修", "失败"],
    "memory.remember_preference": ["记住", "以后", "偏好", "习惯", "下次", "别忘", "我喜欢"],
    "skill.self_evolve": ["进化", "自进化", "改技能", "自动改写", "越来越懂", "学会", "复盘"],
    "automation.flow": ["自动化", "定时", "每天", "触发", "流程", "流水线", "计划任务", "提醒"],
    "integration.external_service": ["api", "mcp", "数据库", "同步", "外部", "notion", "gmail", "slack"],
    "media.create_content": ["图片", "画图", "视频", "语音", "配音", "生成", "文生图", "文生视频"],
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _term_hits(text: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    for term in terms:
        item = _normalize(term)
        if item and item in text and item not in hits:
            hits.append(term)
    return hits


def _score_capability(text: str, cap: CapabilityMetadata) -> tuple[float, list[str]]:
    terms: list[str] = []
    terms.extend(cap.get("example_utterances", []))
    terms.extend([cap.get("title", ""), cap.get("description", "")])
    terms.extend(DOMAIN_HINTS.get(cap["id"], []))

    hits = _term_hits(text, terms)
    if not hits:
        return 0.0, []

    score = 0.0
    for hit in hits:
        length_bonus = min(len(hit), 12) / 24
        score += 0.6 + length_bonus

    # Prefer explicit capability examples over broad domain words.
    example_hits = _term_hits(text, cap.get("example_utterances", []))
    score += len(example_hits) * 0.8

    # Normalize but keep strong multi-hit matches higher.
    return min(score / 4.0, 1.0), hits[:8]


def _risk_level(matches: list[CapabilityMatch]) -> str:
    if not matches:
        return "safe"
    return max((m["capability"]["risk_level"] for m in matches), key=lambda risk: _RISK_WEIGHT.get(risk, 0))


def _primary_intent(capability_id: str | None) -> str:
    if not capability_id:
        return "unknown"
    mapping = {
        "system.eye_comfort": "environment_comfort",
        "desktop.app_control": "desktop_control",
        "browser.web_task": "browser_automation",
        "files.organize_workspace": "file_workspace",
        "project.health_check": "project_health",
        "project.self_repair_plan": "project_self_repair",
        "memory.remember_preference": "remember_preference",
        "skill.self_evolve": "skill_evolution",
        "automation.flow": "automation_flow",
        "integration.external_service": "external_integration",
        "media.create_content": "media_generation",
    }
    return mapping.get(capability_id, capability_id.replace(".", "_"))


def route_intent(user_text: str, *, max_matches: int = 4) -> IntentRoute:
    text = _normalize(user_text)
    raw_matches: list[CapabilityMatch] = []
    for cap in list_capabilities():
        if not cap.get("enabled", True):
            continue
        score, hits = _score_capability(text, cap)
        if score <= 0:
            continue
        raw_matches.append({"capability": cap, "score": round(score, 3), "matched_terms": hits})

    raw_matches.sort(
        key=lambda item: (
            item["score"],
            -_RISK_WEIGHT.get(item["capability"]["risk_level"], 0),
            item["capability"]["id"],
        ),
        reverse=True,
    )
    matches = raw_matches[: max(1, int(max_matches or 4))]
    top = matches[0] if matches else None
    risk = _risk_level(matches)
    confidence = top["score"] if top else 0.0
    needs_confirmation = any(m["capability"].get("requires_confirmation", False) for m in matches)

    plan: list[dict[str, Any]] = []
    if top:
        for idx, match in enumerate(matches, start=1):
            cap = match["capability"]
            plan.append(
                {
                    "step": idx,
                    "capability_id": cap["id"],
                    "title": cap["title"],
                    "risk_level": cap["risk_level"],
                    "requires_confirmation": cap["requires_confirmation"],
                    "tool_candidates": cap["tool_names"],
                    "verification": cap["verification"],
                    "why": match["matched_terms"],
                }
            )
    else:
        plan.append(
            {
                "step": 1,
                "capability_id": "clarify_or_general_chat",
                "title": "继续理解需求",
                "risk_level": "safe",
                "requires_confirmation": False,
                "tool_candidates": [],
                "verification": ["询问缺失约束，或按普通对话回答"],
                "why": [],
            }
        )

    notes = []
    if needs_confirmation:
        notes.append("匹配到需要确认的能力；执行真实桌面、外部写入或文件写入前必须确认。")
    if confidence < 0.45:
        notes.append("置信度偏低；建议先展示计划或询问一句关键约束。")

    return {
        "user_text": user_text,
        "primary_intent": _primary_intent(top["capability"]["id"] if top else None),
        "confidence": confidence,
        "needs_confirmation": needs_confirmation,
        "risk_level": risk,
        "matches": matches,
        "plan": plan,
        "notes": notes,
    }
