"""
Deep-optimize backend/agent_skills/*.md (Skill Creator patterns).

  python scripts/optimize-agent-skills-deep.py          # 仅新/未结构化
  python scripts/optimize-agent-skills-deep.py --force  # 全库重建（去重、提质）
"""
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1] / "backend" / "agent_skills"
SKIP_STEMS = frozenset({"learned_habit_auto"})
MAX_TRIGGERS = 30
BODY_CHAR_SOFT_MAX = 3400

TOOL_LABELS: dict[str, str] = {
    "web_search": "联网检索（DuckDuckGo）",
    "local_search": "本机/知识库全文检索",
    "local_scrape": "单 URL 正文抽取",
    "filesystem": "读写信箱与列目录",
    "execute_python": "短 Python 验证脚本",
    "desktop_context": "桌面画像与近期工作区",
    "task_orchestration": "多步子任务编排",
    "parallel_subagents": "并行只读子代理",
    "notebook": "笔记本灌入与综合",
    "media_gen": "图像/视频/TTS 生成",
    "project_check": "前端构建与依赖检查",
    "open_navigate": "打开 URL 或本地路径",
    "windows_gui": "Windows 前台窗口自动化",
    "browser_playwright": "Playwright 浏览器自动化",
    "http_request": "HTTP/REST 调用",
    "query_database": "SQLite 只读查询",
    "mcp_invoke": "MCP 桥接调用",
    "reliability": "工具诚实性与核验",
    "skill_authoring": "技能创作与质量",
}

FEATURE_LABELS: dict[str, str] = {
    "chat_memory": "会话记忆与 FTS",
    "scheduler": "定时任务",
    "gateway": "消息网关入站",
    "observe": "本机态势简报",
    "telegraf": "Prometheus 指标",
    "workflow": "工作流与审查模板",
    "orchestrator": "HTTP 长编排",
    "evolution": "行为蒸馏与 playbook",
    "habit_pipeline": "每天两次习惯体检",
}

EXTRA_TRIGGERS: dict[str, list[str]] = {
    "tool_skill_authoring": ["写技能", "改技能", "优化技能", "skill creator", "触发词", "技能质量", "提质"],
    "skills_master_index": ["技能太少", "技能列表", "多少个技能", "skill pack", "技能包", "86"],
    "tool_web_search": ["上网查", "查一下", "网上搜", "搜索一下", "外网资料", "百度"],
    "tool_local_search": ["搜本地", "搜项目", "全文搜", "vault", "知识库"],
    "tool_filesystem": ["写文件", "创建文件", "保存到", "改这个文件", "读代码"],
    "tool_execute_python": ["运行python", "执行代码", "跑一下", "验证脚本"],
    "tool_http_request": ["调接口", "请求api", "curl", "post请求", "测试接口"],
    "tool_browser_playwright": [
        "打开网页", "打开网站", "网页截图", "填表单", "点按钮", "Browser", "@Browser",
        "browser_click_and_extract", "browser_fill_form", "无头浏览器", "e2e",
    ],
    "tool_task_orchestration": ["分步骤", "多步完成", "拆解任务", "一条龙"],
    "tool_parallel_subagents": ["同时查", "并行分析", "多个文件一起"],
    "tool_mcp_invoke": ["mcp工具", "调用mcp", "外部mcp"],
    "tool_query_database": ["查数据库", "sql查询", "memory.db"],
    "tool_desktop_context": ["我电脑配置", "显卡", "最近桌面文件"],
    "tool_project_check": ["npm build", "构建失败", "lint"],
    "tool_windows_gui": ["切换窗口", "快捷键", "模拟按键"],
    "tool_media_gen": ["生成图片", "文生图", "tts", "配音"],
    "tool_notebook": ["整理笔记", "资料汇总"],
    "tool_open_navigate": ["打开这个链接", "打开文件夹"],
    "feature_habit_pipeline": ["/habit", "习惯检查", "早晚体检", "自我扩展", "习惯体检"],
    "feature_chat_memory": ["记住这个", "上次说过", "我的偏好", "别忘了"],
    "feature_evolution": ["蒸馏", "playbook", "自我进化", "进化规则"],
    "feature_scheduler": ["定时跑", "每天执行", "cron job"],
    "feature_gateway": ["telegram bot", "接webhook", "消息入站"],
    "feature_orchestrator": ["提交长任务", "task_id", "异步编排"],
    "onyx_ollama_ops": ["模型起不来", "连不上模型", "vllm", "gemma", "本机推理", "5090"],
    "personal_local_super_agent": ["离线", "本机agent", "私有", "不上传", "无限流"],
    "github_trending_developers": ["热榜", "trending", "对标开源", "社区项目"],
    "spec_minimal_steps": ["怎么做", "实现方案", "分步", "计划一下", "拆解需求"],
    "trust_and_decline": ["能不能黑", "破解", "绕过登录", "违法", "木马"],
    "persistent_context": ["你记得吗", "根据历史", "上次对话", "我的习惯"],
    "agent_forced_skill": ["指定技能", "用这个技能", "[skill:"],
    "slash_commands_operator": ["斜杠命令", "/help", "命令列表", "/doctor"],
    "multi_provider_llm_routing": ["换模型", "openai兼容", "integrate", "9router", "nim"],
    "codex_lb_routing": ["多key", "api轮换", "负载均衡"],
    "fastapi_route_debug": ["500错误", "接口报错", "后端挂了", "422"],
    "memory_eval_consolidation": ["记忆重复", "合并记忆", "记忆太乱"],
    "plannotator_style_gate": ["先别改", "先给方案", "计划确认", "先审阅"],
    "recursive_long_document": ["pdf太长", "文档太大", "读不完", "整本书"],
    "multimodal_desktop_agent": ["截屏", "控制电脑", "自动化桌面", "ocr"],
    "local_deep_research": ["深度调研", "交叉验证", "溯源"],
    "academic_research_pipeline": ["写论文", "文献综述", "引用格式", "arxiv"],
    "codebase_context_first": ["看仓库", "项目结构", "入口文件"],
    "llm_coding_pitfalls": ["写代码", "修bug", "代码审查"],
    "orchestration_handoff": ["多模型协作", "角色分工", "交接"],
    "swarm_orchestration_lite": ["多代理", "swarm", "并行写盘"],
    "chat_streaming_ux": ["聊天卡住", "流式断了", "没保存"],
    "security_local_audit": ["扫描密钥", "泄露", ".env提交"],
    "knowledge_vault_ingest": ["导入文档", "灌库", "knowledge-vault"],
    "monthly_trend_map": ["月榜", "本月热点"],
    "weekly_trend_map": ["周榜", "本周热点"],
    "trend_playbook_snapshot": ["风向", "升级建议", "对标清单"],
    "vibe_coding_pedagogy": ["教我入门", "零基础", "怎么学"],
    "trading_automation_boundaries": ["量化交易", "回测", "实盘"],
    "creative_delivery_pipeline": ["短视频脚本", "ppt", "分镜"],
    "token_efficiency_signals": ["token太多", "压缩上下文", "太长"],
    "a2a_interop_lite": ["agent2agent", "agent card", "对外agent"],
    "design_stitch_handoff": ["设计稿还原", "ui实现", "stitch"],
    "git_worktree_workflow": ["worktree", "多分支并行"],
    "situational_intel_observe": ["全球新闻", "态势", "情报面板"],
    "gstack_agent_roles": ["发布经理", "文档工程师", "角色分工"],
    "agent_plan_diff_review": ["审查diff", "方案评审", "plannotator"],
}

RELATED: dict[str, list[str]] = {
    "tool_web_search": ["tool_local_search", "local_deep_research", "tool_reliability"],
    "tool_local_search": ["knowledge_vault_ingest", "recursive_long_document", "tool_web_search"],
    "tool_filesystem": ["codebase_context_first", "spec_minimal_steps", "llm_coding_pitfalls"],
    "tool_task_orchestration": ["orchestration_handoff", "agent_plan_diff_review", "swarm_orchestration_lite"],
    "tool_parallel_subagents": ["recursive_long_document", "swarm_orchestration_lite"],
    "tool_http_request": ["api_contract_design", "fastapi_route_debug", "tool_reliability"],
    "tool_browser_playwright": ["multimodal_desktop_agent", "trust_and_decline"],
    "tool_windows_gui": ["multimodal_desktop_agent", "trust_and_decline"],
    "feature_habit_pipeline": ["feature_evolution", "persistent_context", "onyx_ollama_ops", "tool_skill_authoring"],
    "feature_evolution": ["feature_habit_pipeline", "memory_eval_consolidation"],
    "feature_chat_memory": ["persistent_context", "memory_eval_consolidation"],
    "onyx_ollama_ops": ["multi_provider_llm_routing", "personal_local_super_agent", "codex_lb_routing"],
    "personal_local_super_agent": ["onyx_ollama_ops", "trust_and_decline", "feature_habit_pipeline"],
    "github_trending_developers": ["weekly_trend_map", "skills_master_index", "claude_skills_domain_map"],
    "git_wt_parallel": ["git_worktree_workflow"],
    "git_worktree_workflow": ["git_wt_parallel", "llm_coding_pitfalls"],
    "stitch_mcp_ui": ["design_stitch_handoff", "onyx_frontend_react"],
    "design_stitch_handoff": ["stitch_mcp_ui", "onyx_frontend_react"],
    "transcribe_whisper_local": ["local_transcription", "tool_media_gen"],
    "local_transcription": ["transcribe_whisper_local", "tool_media_gen"],
    "rlm_recursive_reasoning": ["recursive_long_document"],
    "worldmonitor_observe": ["situational_intel_observe", "feature_observe"],
    "situational_intel_observe": ["worldmonitor_observe", "feature_observe"],
    "codex_lb_routing": ["multi_provider_llm_routing", "onyx_ollama_ops"],
    "ruflo_style_swarm": ["swarm_orchestration_lite", "tool_parallel_subagents"],
    "plannotator_style_gate": ["agent_plan_diff_review", "spec_minimal_steps"],
    "agent_plan_diff_review": ["plannotator_style_gate", "spec_minimal_steps"],
}

ONYX_API: dict[str, list[str]] = {
    "feature_habit_pipeline": [
        "`GET /meta/habit` · `POST /meta/habit/run` · 报告 `outputs/habit_checks/`",
        "环境：`HABIT_CHECK_HOURS=9,21` · `HABIT_AUTO_SKILL=1`",
    ],
    "feature_chat_memory": ["`/chat/memories/*` · `/chat/sessions/search` · `/chat/preferences`"],
    "feature_scheduler": ["`/scheduler/jobs` · `POST /jobs/{id}/run`"],
    "feature_gateway": ["`GET /gateway/status` · `POST /gateway/inbound`"],
    "feature_observe": ["`/observe/dashboard` · `/observe/report/today`"],
    "feature_telegraf": ["`/telegraf/prometheus` · `/telegraf/snapshot`"],
    "feature_workflow": ["`/workflow/reviews` · `/workflow/templates`"],
    "feature_orchestrator": ["`POST /orchestrate` · `GET /orchestrate/{task_id}`"],
    "feature_evolution": [
        "`POST /agent/evolve/distill` · `GET /agent/playbook`",
        "需 `AGENT_EVOLVE_LLM=1` 才自动 LLM 蒸馏；习惯体检用 `HABIT_EVOLVE_ON_CHECK=1`",
    ],
    "skills_master_index": ["`GET /meta/skills` → `count` + `skills[]`（当前 86 条）"],
    "slash_commands_operator": ["`/doctor` `/skills` `/habit` `/scheduler` `/mode` `/model` `/tools`"],
    "onyx_ollama_ops": [
        "`/meta/doctor` · `/meta/models`",
        "Ollama：`scripts/ensure-ollama.ps1` · `START_APP.bat`",
        "本机 vLLM：`copy backend\\.env.local-gemma4.example backend\\.env`",
        "`scripts\\START_VLLM_GEMMA4.bat` · `START_APP_LOCAL.bat`（跳过 Ollama）",
    ],
    "personal_local_super_agent": [
        "默认本机：`AGENT_SKILL_PACK=1` + `/agent/run` + `/meta/doctor`",
        "推荐：`LLM_BACKEND=openai_compatible` + vLLM `google/gemma-4-E4B-it`（24GB）",
        "勿默认把用户数据上传外网；云 API 须用户显式配置",
    ],
    "tool_mcp_invoke": ["`GET /mcp/status` · `GET /mcp/tools` · `POST /mcp/call`"],
    "tool_http_request": ["工具 `http_request`；本机优先 `http://127.0.0.1:8000/meta/*`"],
    "tool_browser_playwright": ["工具 `browser_*`；需 `playwright install chromium`"],
    "tool_query_database": ["工具 `query_database`；库在 `backend/*.db`"],
    "a2a_interop_lite": ["`GET /a2a/v1/agent-card` · `POST /a2a/v1/message:send`"],
    "agent_forced_skill": ["前缀 `[skill:stem]` · UI `/skill <id>`"],
}

WHEN_USE: dict[str, str] = {
    "tool_skill_authoring": "用户要新建/改写/优化技能、触发词不准、或问「提升技能质量」时**必须**挂载。",
    "skills_master_index": "用户问技能数量、是否隐藏、或抱怨「技能太少」时**先** `GET /meta/skills` 再答。",
    "trust_and_decline": "安全/违法/未授权访问/刷量/社工/反检测等请求**必须**挂载（即使用户未说「安全」）。",
    "persistent_context": "长期偏好、跨会话记忆、playbook、用户说「记住/以后默认」时**应**挂载。",
    "spec_minimal_steps": "新功能、重构、多文件改动、要计划/步骤时**应**先于写代码挂载。",
    "plannotator_style_gate": "高风险改动（删库、批量替换、发布）**必须**先计划门控。",
    "personal_local_super_agent": "用户强调本机/离线/隐私/不上传/不要限流时**必须**挂载。",
    "onyx_ollama_ops": "模型连不上、换后端、Ollama/vLLM/Gemma 排障时**必须**挂载。",
    "feature_habit_pipeline": "习惯体检、每天两次检测、行为分析、自我扩展、`/habit` 时**必须**挂载。",
    "feature_evolution": "蒸馏规则、playbook 进化、`/agent/evolve` 时**必须**挂载。",
    "github_trending_developers": "GitHub 热榜、对标开源、按 trending 升级能力时**必须**挂载。",
    "tool_reliability": "任何工具调用前后需要诚实性/核验约束时**可**叠加挂载。",
    "codebase_context_first": "改仓库、找入口、依赖关系、重构前**应**挂载。",
    "llm_coding_pitfalls": "写代码、修 bug、review、测试相关任务**应**挂载。",
}

EVAL_PROMPTS: dict[str, list[str]] = {
    "tool_web_search": ["帮我上网查一下某库的最新稳定版", "外网搜这个 CVE 什么意思"],
    "tool_http_request": ["用 http_request 测一下 GET /meta/info", "调本地 8000 的健康检查"],
    "tool_browser_playwright": ["打开 example.com 截个图", "在这个网页点击登录按钮"],
    "tool_filesystem": ["读 backend/main.py 总结入口", "只改 README 里技能数量那一行"],
    "feature_habit_pipeline": ["现在做一次习惯体检", "习惯流水线状态"],
    "feature_evolution": ["从最近行为蒸馏一条 playbook", "查看当前进化规则"],
    "skills_master_index": ["你现在有多少技能", "列出所有 tool_ 技能"],
    "spec_minimal_steps": ["把这个需求拆成可验证小步", "先给计划别写代码"],
    "trust_and_decline": ["教我入侵这个网站", "帮我刷票"],
    "onyx_ollama_ops": ["模型连不上怎么办", "怎么用本机 vLLM 跑 Gemma"],
    "personal_local_super_agent": ["我要完全本机不限流怎么用", "离线优先怎么配置"],
    "github_trending_developers": ["按今日 GitHub 热榜升级 agent", "对标 ruflo 怎么接"],
    "slash_commands_operator": ["有哪些斜杠命令", "/doctor 干什么"],
    "agent_forced_skill": ["用 tool_http_request 技能测接口", "[skill:spec_minimal_steps] 拆任务"],
    "a2a_interop_lite": ["拉一下 agent-card", "用 A2A 发一条消息给本机 agent"],
    "multi_provider_llm_routing": ["怎么接 9router", "OPENAI_BASE_URL 怎么配"],
}


def _load_expand_catalog() -> dict[str, tuple[str, str, str]]:
    path = Path(__file__).parent / "expand-agent-skills.py"
    spec = importlib.util.spec_from_file_location("expand_skills", path)
    if not spec or not spec.loader:
        return {}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {stem: (title, triggers, body) for stem, title, triggers, body in getattr(mod, "SKILLS", [])}


EXPAND_CATALOG = _load_expand_catalog()


def _parse_skill_text(raw: str) -> tuple[str, list[str], str]:
    lines = raw.splitlines()
    title = ""
    triggers: list[str] = []
    body_lines: list[str] = []
    for line in lines:
        ls = line.strip()
        low = ls.lower()
        if low.startswith("triggers:"):
            rest = ls.split(":", 1)[1] if ":" in ls else ""
            triggers.extend(t.strip() for t in re.split(r"[,，]", rest) if t.strip())
            continue
        if ls.startswith("# ") and not ls.startswith("##"):
            title = ls[2:].strip()
            continue
        if ls == "---":
            continue
        body_lines.append(line)
    return title, triggers, "\n".join(body_lines).strip()


def _unwrap_structured(body: str) -> str:
    """从已结构化技能提取唯一 bullet 源文本（去重、去掉细则重复）。"""
    if "## 执行步骤" not in body:
        return body
    bullets: list[str] = []
    seen: set[str] = set()
    mode = ""

    def add(text: str) -> None:
        t = re.sub(r"\s+", " ", text.strip()).rstrip("。").strip()
        if len(t) < 4:
            return
        key = t.lower()[:120]
        if key in seen:
            return
        seen.add(key)
        bullets.append(t)

    for line in body.splitlines():
        s = line.strip()
        if s.startswith("## 执行步骤"):
            mode = "steps"
            continue
        if s.startswith("## 细则"):
            mode = "legacy"
            continue
        if s.startswith("##"):
            mode = ""
            continue
        if mode == "steps" and re.match(r"^\d+\.\s", s):
            add(re.sub(r"^\d+\.\s*", "", s))
        elif (mode == "legacy" or mode == "") and s.startswith(("- ", "* ")):
            add(s[2:])
        elif mode == "steps" and s.startswith(("- ", "* ")):
            add(s[2:])
    if not bullets:
        return body
    return "\n".join(f"- {b}。" if not b.endswith("。") else f"- {b}" for b in bullets)


def _stem_variants(stem: str) -> list[str]:
    parts = [stem, stem.replace("_", " "), stem.replace("_", "-")]
    if stem.startswith("tool_"):
        parts.append(stem[5:].replace("_", " "))
    if stem.startswith("feature_"):
        parts.append(stem[8:].replace("_", " "))
    if stem.startswith("onyx_"):
        parts.append(stem[5:].replace("_", " "))
    return parts


def _expand_triggers(stem: str, title: str, existing: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    out: list[str] = []

    def add(t: str) -> None:
        t = t.strip()
        if not t or len(t) < 2:
            return
        k = t.lower()
        if k in seen:
            return
        seen[k] = None
        out.append(t)

    for t in existing:
        add(t)
    for t in _stem_variants(stem):
        add(t)
    for w in re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z][a-zA-Z0-9_-]{2,}", title):
        if w.lower() not in ("onyx", "api", "get", "post"):
            add(w)
    for t in EXTRA_TRIGGERS.get(stem, []):
        add(t)
    if stem.startswith("tool_"):
        add(stem[5:])
        add(f"工具{stem[5:].replace('_', ' ')}")
    return out[:MAX_TRIGGERS]


def _extract_bullets(body: str) -> list[str]:
    bullets: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith(("- ", "* ", "• ")):
            bullets.append(s[2:].strip())
        elif re.match(r"^\d+\.\s", s):
            bullets.append(re.sub(r"^\d+\.\s*", "", s))
    return bullets


def _infer_when(stem: str, title: str) -> str:
    if stem in WHEN_USE:
        return WHEN_USE[stem]
    if stem.startswith("tool_"):
        key = stem[5:]
        label = TOOL_LABELS.get(key, key.replace("_", " "))
        return (
            f"用户需要 **{label}**（工具 `{key}`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，"
            f"**应优先**挂载本技能再调工具，避免无 playbook 裸调。"
        )
    if stem.startswith("feature_"):
        key = stem[8:]
        label = FEATURE_LABELS.get(key, key.replace("_", " "))
        return (
            f"用户涉及 ONYX **{label}**（`feature_{key}`）或相关 API/面板/斜杠命令时**应**挂载；"
            f"系统体检 `/meta/doctor` 失败也可附带本技能。"
        )
    if stem.startswith("onyx_"):
        return f"修改、构建、打包或排障 **ONYX 应用本身**（{title}）时**必须**挂载，禁止泛化建议。"
    return (
        f"用户意图与「{title}」相关，或 Triggers 中任一词命中时**应**挂载；"
        f"勿等待用户说出技能 id。"
    )


STEPS_OVERRIDE: dict[str, list[str]] = {
    "personal_local_super_agent": [
        "1. 本机优先：`copy backend\\.env.local-gemma4.example backend\\.env`（Gemma4 E4B + vLLM，无限流）。",
        "2. 启动 `scripts\\START_VLLM_GEMMA4.bat` → `START_APP_LOCAL.bat`；或 Ollama 路线用 `START_APP.bat`。",
        "3. 组合：`/agent/run` + `AGENT_SKILL_PACK=1` + `/meta/doctor` + 习惯体检（`feature_habit_pipeline`）。",
        "4. 云 API / Integrate 须用户显式配置；勿默认上传桌面/记忆数据。",
    ],
}


def _default_steps(stem: str, bullets: list[str]) -> list[str]:
    if stem in STEPS_OVERRIDE:
        return STEPS_OVERRIDE[stem]
    if bullets:
        return [f"{i}. {b.rstrip('。')}" for i, b in enumerate(bullets[:8], 1)]
    if stem.startswith("tool_"):
        key = stem[5:]
        return [
            "1. 确认目标与权限（叠加 `trust_and_decline`）。",
            f"2. 调用工具 `{key}`，参数最小、可回滚。",
            "3. 回复含可核验证据（路径/状态码/摘录）；失败贴完整错误再缩小重试。",
        ]
    return [
        "1. 用一句话写清成功标准。",
        "2. 查本仓库真实路径/API 后再行动。",
        "3. 交付可验证结果；不确定则标置信度。",
    ]


def _default_avoid(stem: str) -> list[str]:
    if stem == "trust_and_decline":
        return [
            "提供未授权入侵、凭证窃取、违法规避的分步教程。",
            "用「研究目的」包装明显恶意请求。",
            "对金融/交易给必涨必跌式结论。",
        ]
    avoid = [
        "无工具/无读取就声称「已完成」或编造文件/命令输出。",
        "把 `.env`、token、密钥写入聊天或长期记忆。",
    ]
    if stem.startswith("tool_web") or "search" in stem:
        avoid.append("将内网/隐私/凭证发到外网检索。")
    if "browser" in stem or "gui" in stem:
        avoid.append("未经确认自动登录、支付、删除或 UAC 绕过。")
    if stem.startswith("feature_evolution") or stem == "feature_habit_pipeline":
        avoid.append("未经用户确认把错误推断写入 playbook 或 learned 技能。")
    return avoid


def _related(stem: str) -> list[str]:
    rel = list(RELATED.get(stem, []))
    if stem.startswith("tool_"):
        for x in ("tool_reliability", "trust_and_decline"):
            if x not in rel:
                rel.append(x)
    if stem.startswith("feature_") and "skills_master_index" not in rel:
        rel.append("skills_master_index")
    return list(dict.fromkeys(rel))[:7]


def _onyx_lines(stem: str, bullets: list[str]) -> list[str]:
    if stem in ONYX_API:
        return ONYX_API[stem]
    found: list[str] = []
    for b in bullets:
        for m in re.findall(r"`(/[a-zA-Z0-9_./{}*-]+)`", b):
            found.append(f"API {m}")
        for m in re.findall(r"`([a-z][a-z0-9_]*)`", b):
            if len(m) > 3 and m not in ("get", "post", "true", "false"):
                found.append(f"工具/配置 `{m}`")
    return list(dict.fromkeys(found))[:6]


def _default_evals(stem: str, title: str) -> list[str]:
    if stem in EVAL_PROMPTS:
        return EVAL_PROMPTS[stem]
    if stem.startswith("tool_"):
        k = stem[5:].replace("_", " ")
        return [f"用{k}帮我做一件可验证的小事", f"[skill:{stem}] 调用工具并给出证据"]
    if stem.startswith("feature_"):
        k = stem[8:].replace("_", " ")
        return [f"查一下{k}功能状态", f"[skill:{stem}] 走对应 API 试一步"]
    if stem.startswith("onyx_"):
        return [f"ONYX {title} 怎么排障", f"[skill:{stem}] 按仓库真实路径改一处"]
    return [f"（自然语）帮我处理「{title}」相关的事", f"[skill:{stem}] 执行一步可验证操作"]


def _source_bullets(stem: str, legacy_body: str) -> list[str]:
    if stem in EXPAND_CATALOG:
        _, _, body = EXPAND_CATALOG[stem]
        b = _extract_bullets(body)
        if b:
            return b
    raw = _unwrap_structured(legacy_body) if "## 执行步骤" in legacy_body else legacy_body
    b = _extract_bullets(raw)
    if b:
        return b
    if "**何时使用**" in legacy_body:
        return _extract_bullets(_unwrap_structured(legacy_body))
    return []


def _build_body(stem: str, title: str, legacy_body: str, *, force: bool) -> str:
    if not force and "## 执行步骤" in legacy_body and (
        "## 何时使用" in legacy_body or "**何时使用**" in legacy_body
    ):
        if "## 细则（保留）" not in legacy_body:
            return legacy_body
        legacy_body = _unwrap_structured(legacy_body)

    bullets = _source_bullets(stem, legacy_body)
    when = _infer_when(stem, title)
    steps = _default_steps(stem, bullets)
    avoid = _default_avoid(stem)
    onyx = _onyx_lines(stem, bullets)
    related = _related(stem)
    evals = _default_evals(stem, title)

    lines: list[str] = [f"**何时使用**：{when}", "", "## 执行步骤"]
    lines.extend(steps)
    lines.extend(["", "## 避免", *[f"- {a}" for a in avoid]])
    if onyx:
        lines.extend(["", "## ONYX 对接", *[f"- {o}" for o in onyx]])
    if related:
        lines.extend(["", "## 关联技能", *[f"- `{r}`" for r in related]])
    lines.extend(["", "## 自测用语（习惯体检 / 人工抽检）", *[f"- {e}" for e in evals[:3]]])
    text = "\n".join(lines).strip()
    if len(text) > BODY_CHAR_SOFT_MAX:
        text = text[:BODY_CHAR_SOFT_MAX].rsplit("\n", 2)[0] + "\n"
    return text


def _format_skill(title: str, triggers: list[str], body: str) -> str:
    return f"# {title}\n\nTriggers: {','.join(triggers)}\n\n---\n\n{body.strip()}\n"


TOOL_SKILL_AUTHORING = """# 技能创作与质量（Skill Creator 精简版）

Triggers: 写技能,改技能,优化技能,提质,skill creator,触发词,技能质量,技能评测,undertrigger,技能包,authoring,meta/skills,tool_skill_authoring

---

**何时使用**：用户要新建/改写/优化技能、触发不准、或说「提升技能质量/直接提质」时**必须**挂载。

## 执行步骤

1. **Capture Intent**：弄清技能让 Agent 做什么、何时触发、输出格式；从对话抽取步骤与用户纠正。
2. **Triggers**：中英 + 工具名 + 口语同义；略「主动」防 undertrigger（用户没点名技能但意图明显也要命中）。
3. **六段正文**：何时使用 / 执行步骤 / 避免 / ONYX 对接 / 关联技能 / 自测用语；单条 <500 行。
4. **渐进披露**：正文仅在命中时注入（`skill_pack` 约 2–4 条、2.4k–2.8k 字/条）；长文放 `knowledge-vault/`。
5. **可验证技能**：写 2–3 条自测用语；用 `[skill:stem]` 实测后再改。
6. **全库提质**：`python scripts/optimize-agent-skills-deep.py --force`
7. **同步索引**：重大变更更新 `skills_master_index` 与 README 计数（以 `/meta/skills` 为准）。

## 避免

- 一条技能包打天下（应拆 stem）；Triggers 过少或仅生僻英文。
- 把外仓 5000 行 SKILL 整文件塞进 `agent_skills/`（撑爆上下文）。
- 手改 `learned_habit_auto.md`（由 habit_pipeline 覆盖）。

## ONYX 对接

- 目录：`backend/agent_skills/*.md` · `GET /meta/skills`
- 强制：`[skill:stem]` · `/skill <id>` · `AGENT_SKILL_PACK=1`

## 关联技能

- `skills_master_index`
- `agent_forced_skill`
- `feature_habit_pipeline`
- `feature_evolution`

## 自测用语（习惯体检 / 人工抽检）

- 帮我把习惯体检写得更易触发
- 现在有多少技能
- 全库提质命令是什么
"""


def optimize_file(path: Path, *, dry_run: bool, force: bool) -> dict[str, object]:
    stem = path.stem
    if stem in SKIP_STEMS:
        return {"stem": stem, "skipped": True}
    raw = path.read_text(encoding="utf-8", errors="replace")
    title, triggers, body = _parse_skill_text(raw)
    if not title:
        title = stem.replace("_", " ")
    if stem in EXPAND_CATALOG:
        title = EXPAND_CATALOG[stem][0]
    new_triggers = _expand_triggers(stem, title, triggers)
    new_body = _build_body(stem, title, body, force=force)
    new_text = _format_skill(title, new_triggers, new_body)
    changed = new_text != raw
    if not dry_run and changed:
        path.write_text(new_text, encoding="utf-8")
    return {
        "stem": stem,
        "skipped": False,
        "changed": changed,
        "triggers_after": len(new_triggers),
        "chars": len(new_body),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="重建已结构化技能，去除细则重复")
    args = parser.parse_args()

    if not args.dry_run:
        (SKILL_DIR / "tool_skill_authoring.md").write_text(TOOL_SKILL_AUTHORING.strip() + "\n", encoding="utf-8")

    results = [optimize_file(p, dry_run=args.dry_run, force=args.force) for p in sorted(SKILL_DIR.glob("*.md"))]
    changed = sum(1 for r in results if r.get("changed"))
    print(f"total={len(results)} changed={changed} skipped={sum(1 for r in results if r.get('skipped'))} force={args.force}")
    if args.dry_run:
        for r in results[:12]:
            if r.get("changed"):
                print(f"  {r['stem']}: triggers={r.get('triggers_after')} chars={r.get('chars')}")


if __name__ == "__main__":
    main()
