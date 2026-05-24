"""Capability registry for BKLT Blacklight.

Tools are low-level actions. Capabilities are user-facing intents such as
"make the screen easier on my eyes", "organize my desktop", or "repair this
project". This import-safe module lets the UI and router reason about what
Blacklight can do before touching real tools.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Literal, TypedDict

RiskLevel = Literal["safe", "confirm", "dangerous"]
CapabilityDomain = Literal[
    "system",
    "desktop",
    "browser",
    "files",
    "project",
    "memory",
    "skill",
    "automation",
    "integration",
    "media",
]


class CapabilityMetadata(TypedDict):
    id: str
    domain: CapabilityDomain
    title: str
    description: str
    example_utterances: list[str]
    tool_names: list[str]
    risk_level: RiskLevel
    requires_confirmation: bool
    verification: list[str]
    enabled: bool


CAPABILITIES: dict[str, CapabilityMetadata] = {
    "system.eye_comfort": {
        "id": "system.eye_comfort",
        "domain": "system",
        "title": "护眼/舒适显示",
        "description": "把屏幕刺眼、夜间使用、护眼、太亮等自然语言路由到系统显示舒适度能力。第一版先规划和安全回退，后续接 Windows 夜间模式、亮度和主题 API。",
        "example_utterances": ["护眼模式", "屏幕太刺眼", "帮我调暗一点", "晚上模式", "眼睛不舒服"],
        "tool_names": ["get_device_profile", "get_foreground_window", "open_path", "send_hotkey"],
        "risk_level": "confirm",
        "requires_confirmation": True,
        "verification": ["读取前台窗口或系统反馈", "记录用户显示偏好", "必要时提示系统设置权限"],
        "enabled": True,
    },
    "desktop.app_control": {
        "id": "desktop.app_control",
        "domain": "desktop",
        "title": "桌面 App 控制",
        "description": "切换窗口、输入文字、发送快捷键、打开文件或程序等本机桌面操作。",
        "example_utterances": ["切到浏览器", "打开桌面那个文件", "给当前窗口输入这段话", "按 Ctrl+S"],
        "tool_names": ["list_windows", "focus_window", "open_path", "type_text", "send_hotkey", "click_screen"],
        "risk_level": "dangerous",
        "requires_confirmation": True,
        "verification": ["读取前台窗口", "确认目标窗口标题", "危险输入前要求确认"],
        "enabled": True,
    },
    "browser.web_task": {
        "id": "browser.web_task",
        "domain": "browser",
        "title": "网页浏览与操作",
        "description": "打开网页、搜索、抓取、截图、点击、填写表单等浏览器任务。",
        "example_utterances": ["打开这个网页看看", "帮我填这个表", "截个网页图", "点一下网页里的按钮"],
        "tool_names": [
            "web_search",
            "local_scrape_url",
            "browser_navigate",
            "browser_playwright",
            "browser_screenshot",
            "browser_fill_form",
        ],
        "risk_level": "dangerous",
        "requires_confirmation": True,
        "verification": ["提取页面正文或截图", "提交/付款/删除前必须确认"],
        "enabled": True,
    },
    "files.organize_workspace": {
        "id": "files.organize_workspace",
        "domain": "files",
        "title": "文件与桌面整理",
        "description": "整理桌面、读取文件、列目录、写入报告、处理最近文件。",
        "example_utterances": ["整理桌面", "看看下载里有什么", "读取这个文件", "把结果写成报告"],
        "tool_names": ["list_files", "read_file", "write_file", "get_recent_desktop_files"],
        "risk_level": "confirm",
        "requires_confirmation": True,
        "verification": ["列出变更前后文件", "写入前确认路径", "避免删除和覆盖"],
        "enabled": True,
    },
    "project.health_check": {
        "id": "project.health_check",
        "domain": "project",
        "title": "项目健康检查",
        "description": "运行项目检查、测试、构建和仓库状态读取，适合黑光自检。",
        "example_utterances": ["检查一下项目", "黑光哪里坏了", "跑一下测试", "看看 Git 状态"],
        "tool_names": ["run_project_check", "run_task_orchestration", "execute_python"],
        "risk_level": "safe",
        "requires_confirmation": False,
        "verification": ["返回退出码", "保存检查摘要", "失败时生成修复计划"],
        "enabled": True,
    },
    "project.self_repair_plan": {
        "id": "project.self_repair_plan",
        "domain": "project",
        "title": "项目自修复计划",
        "description": "根据测试、构建或运行日志生成修复计划；第一版不自动写文件，先产出可审查方案。",
        "example_utterances": ["你自己修一下", "自动优化黑光", "根据报错改一下", "失败了自己找原因"],
        "tool_names": ["run_project_check", "read_file", "local_search", "run_parallel_subagents"],
        "risk_level": "confirm",
        "requires_confirmation": True,
        "verification": ["先生成修复计划", "补丁应用后重跑测试", "写入复盘 lesson"],
        "enabled": True,
    },
    "memory.remember_preference": {
        "id": "memory.remember_preference",
        "domain": "memory",
        "title": "记住偏好与习惯",
        "description": "把用户长期偏好、常用流程、执行风格写入记忆和习惯画像。",
        "example_utterances": ["以后都这样", "记住我喜欢", "下次别再", "我一般晚上"],
        "tool_names": ["get_evolution_profile", "notebook_ingest", "get_recent_work_summary"],
        "risk_level": "confirm",
        "requires_confirmation": True,
        "verification": ["写入后可在进化画像中看到", "避免记录隐私敏感内容"],
        "enabled": True,
    },
    "skill.self_evolve": {
        "id": "skill.self_evolve",
        "domain": "skill",
        "title": "技能自进化",
        "description": "把任务复盘、失败教训、使用习惯转成技能改写候选，后续通过 diff 和版本回滚落地。",
        "example_utterances": ["自己进化", "根据习惯改技能", "以后自动改进", "把这次经验记成技能"],
        "tool_names": ["get_evolution_profile", "run_task_orchestration", "notebook_synthesize"],
        "risk_level": "confirm",
        "requires_confirmation": True,
        "verification": ["生成技能提案", "展示 diff", "通过测试后再应用"],
        "enabled": True,
    },
    "automation.flow": {
        "id": "automation.flow",
        "domain": "automation",
        "title": "自动化流程",
        "description": "把定时、触发器、条件、重试、人工确认组合成可复用流程。",
        "example_utterances": ["每天提醒我", "以后自动检查", "触发时执行", "做成流程"],
        "tool_names": ["run_project_check", "run_task_orchestration", "mcp_invoke"],
        "risk_level": "confirm",
        "requires_confirmation": True,
        "verification": ["保存流程定义", "记录每次运行", "失败自动重试或提醒"],
        "enabled": True,
    },
    "integration.external_service": {
        "id": "integration.external_service",
        "domain": "integration",
        "title": "外部服务集成",
        "description": "通过 HTTP、数据库、MCP 连接 GitHub、Notion、Gmail、Slack、第三方 API 或本地服务。",
        "example_utterances": ["同步到 GitHub", "调用这个 API", "查数据库", "用 MCP 工具"],
        "tool_names": ["http_request", "query_database", "mcp_invoke"],
        "risk_level": "dangerous",
        "requires_confirmation": True,
        "verification": ["检查授权", "写操作前确认", "记录外部响应"],
        "enabled": True,
    },
    "media.create_content": {
        "id": "media.create_content",
        "domain": "media",
        "title": "内容生成",
        "description": "生成图片、视频、语音或把素材合成为可预览输出。",
        "example_utterances": ["做张图", "生成视频", "转成语音", "把这些图片做成视频"],
        "tool_names": ["generate_image", "generate_video", "generate_ai_video", "text_to_speech"],
        "risk_level": "confirm",
        "requires_confirmation": True,
        "verification": ["返回 outputs 路径", "检查文件是否生成", "前端预览"],
        "enabled": True,
    },
}


def list_capabilities() -> list[CapabilityMetadata]:
    return [deepcopy(CAPABILITIES[key]) for key in sorted(CAPABILITIES)]


def get_capability(capability_id: str) -> CapabilityMetadata:
    if capability_id not in CAPABILITIES:
        raise KeyError(f"Unknown capability: {capability_id}")
    return deepcopy(CAPABILITIES[capability_id])


def validate_capabilities(known_tools: set[str] | None = None) -> list[str]:
    problems: list[str] = []
    for capability_id, cap in CAPABILITIES.items():
        if cap["id"] != capability_id:
            problems.append(f"{capability_id} has mismatched id {cap['id']}")
        if not cap.get("tool_names"):
            problems.append(f"{capability_id} has no tools")
        if cap["risk_level"] not in {"safe", "confirm", "dangerous"}:
            problems.append(f"{capability_id} has invalid risk level")
        if known_tools is not None:
            for tool in cap["tool_names"]:
                if tool not in known_tools:
                    problems.append(f"{capability_id} references unknown tool: {tool}")
    return problems
