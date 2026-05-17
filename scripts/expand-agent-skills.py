"""One-shot generator: backend/agent_skills/*.md (skip if file exists)."""
from __future__ import annotations

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1] / "backend" / "agent_skills"

SKILLS: list[tuple[str, str, str, str]] = [
    # (stem, title, triggers, body markdown without front matter)
    (
        "skills_master_index",
        "技能总目录（本仓库）",
        "技能库,全部技能,有多少技能,skill catalog,skills list,meta/skills",
        """当用户问「有多少技能」「技能太少」时，先说明事实再指路：

- **权威计数**：`GET /meta/skills` → `count` 与 `skills[]`（与 `backend/agent_skills/*.md` 一一对应，无隐藏过滤）。
- **分类**：
  - **趋势/社区**：`github_trending_developers`、`weekly_trend_map`、`monthly_trend_map`、`trend_playbook_snapshot`
  - **工具专精**：`tool_*` 系列（每个 Agent 工具一条 playbook）
  - **能力/API**：`feature_*` 系列（记忆、定时、网关、观测、工作流等）
  - **垂直/工程**：`onyx_*`、`npm_supply_chain_safety` 等
- **强制挂载**：`[skill:stem]` 或 UI `/skill <id>` / 技能面板点击。
- **自动挂载**：用户消息命中 `Triggers:` 关键词；无命中时回退 `persistent_context` 等默认条。

不克隆外仓正文；外网 claude-skills 类仓库仅作主题对照，落地能力以本仓库 API 为准。""",
    ),
    (
        "tool_web_search",
        "工具：web_search",
        "web_search,联网搜索,duckduckgo,ddg,外网查",
        """- 用于**可公开检索**的事实；敏感/内网数据勿走外网。
- 返回可能过时：结论写「检索时间敏感」并建议二次 `local_search` 交叉。
- 与 `local_search` 分工：外网广度 vs 本机/已索引深度。""",
    ),
    (
        "tool_local_search",
        "工具：local_search 与抓取",
        "local_search,local_scrape,本地搜索,知识库,全文检索",
        """- `local_search`：优先查本机索引与 `knowledge-vault`；长材料配合 `recursive_long_document` 分块。
- `local_scrape_url`：单 URL 正文抽取，设 `max_chars` 防撑爆上下文。
- 多源结论需标注路径/文件名，禁止编造未读文件内容。""",
    ),
    (
        "tool_filesystem",
        "工具：读写与列目录",
        "read_file,write_file,list_files,改代码,读文件,列目录",
        """- 改前先 `list_files` 定位，再 `read_file` 相关入口；禁止未读大段重写。
- `write_file` 保持与仓库风格一致；一次改动聚焦一个意图。
- 默认目录参数为空时用桌面路径；项目任务应显式传项目根路径。""",
    ),
    (
        "tool_execute_python",
        "工具：execute_python",
        "execute_python,跑脚本,验证,python REPL",
        """- 仅短脚本验证（断言、解析、小实验）；长任务拆步。
- 副作用（写盘、删文件）需用户意图明确；失败贴**完整 traceback** 再缩小范围重试。""",
    ),
    (
        "tool_desktop_context",
        "工具：桌面上下文画像",
        "get_device_profile,get_recent_desktop,work_summary,evolution_profile,桌面文件,最近工作",
        """- `get_device_profile`：OS/GPU/路径能力，回答环境相关问题时先拉取。
- `get_recent_desktop_files` / `get_recent_work_summary`：辅助理解用户当前工作区，不代替用户授权读隐私目录。
- `get_evolution_profile`：长期偏好与进化摘要；与 `/chat/memories` 互补。""",
    ),
    (
        "tool_task_orchestration",
        "工具：run_task_orchestration",
        "run_task_orchestration,编排,多步任务,子任务分解",
        """- 复杂目标先拆 3–7 步，每步有可验证产物（文件/命令输出/HTTP 状态）。
- 与 `agent_plan_diff_review` 联用：高风险步骤先出计划再执行。
- 单写者原则：并行子任务勿同时改同一文件（见 `swarm_orchestration_lite`）。""",
    ),
    (
        "tool_parallel_subagents",
        "工具：run_parallel_subagents",
        "run_parallel_subagents,并行子代理,parallel agents",
        """- 用于**只读**或**分区明确**的子问题（多文件摘要、多 URL 对比）。
- 合并结果时去重矛盾陈述；写入操作由主 Agent 串行执行。
- 超长文档分块策略见 `recursive_long_document`。""",
    ),
    (
        "tool_notebook",
        "工具：notebook 摄取与综合",
        "notebook_ingest,notebook_synthesize,笔记本,资料汇总",
        """- `notebook_ingest`：批量灌入片段；`notebook_synthesize`：生成结构化摘要。
- 输出保留来源标签；科研场景叠加 `academic_research_pipeline`。""",
    ),
    (
        "tool_media_gen",
        "工具：图像/视频/TTS",
        "generate_image,generate_video,text_to_speech,出图,配音",
        """- 生成前确认用途合法、无未授权肖像/商标滥用。
- 产物路径写入回复；失败时检查 Ollama/本地模型与 `outputs/` 权限。
- 语音**输入**见 `local_transcription`；`text_to_speech` 为输出。""",
    ),
    (
        "tool_project_check",
        "工具：run_project_check",
        "run_project_check,lint,构建检查,frontend check,npm audit",
        """- `target=frontend`：适合 React/Electron 构建与依赖健康检查思路。
- 供应链安全主题叠加 `npm_supply_chain_safety`。
- 检查失败：贴关键错误行，给最小修复建议，不声称已绿构建除非工具返回成功。""",
    ),
    (
        "tool_open_navigate",
        "工具：open_url 与 open_path",
        "open_url,open_path,打开链接,打开文件夹",
        """- 仅打开用户明确同意的 URL/路径；`file://` 注意 Windows 路径转义。
- 不用于批量打开未知来源链接或钓鱼排查外的自动点击链。""",
    ),
    (
        "tool_windows_gui",
        "工具：Windows 桌面自动化",
        "focus_window,send_hotkey,type_text,click_screen,list_windows,前台窗口",
        """- 与 `multimodal_desktop_agent` 一致：先确认目标应用与授权。
- 优先键盘/焦点路径；坐标点击易碎。
- 高风险弹窗/UAC 绕过请求走 `trust_and_decline`。""",
    ),
    (
        "tool_browser_playwright",
        "工具：Playwright 浏览器",
        "browser_navigate,browser_screenshot,browser_click,browser_fill,playwright",
        """- 先 `browser_navigate` 再交互；关键步骤 `browser_screenshot` 留证。
- `browser_fill_form`：字段选择器需可验证；登录态不硬编码密码到回复。
- 反爬/绕过检测用于不当用途 → 拒绝。""",
    ),
    (
        "tool_http_request",
        "工具：http_request",
        "http_request,REST,API 调用,webhook 测试,fetch",
        """- 默认 GET；写操作需用户确认目标与 body。
- 超时用 `timeout_sec`；响应过大时摘要 status + 关键字段，勿全文塞满上下文。
- 内网/本机 API 优先（如 `/meta/*`、`/agent/*`）而非臆造外网端点。""",
    ),
    (
        "tool_query_database",
        "工具：query_database",
        "query_database,sqlite,SQL,查库,memory.db",
        """- 仅 **SELECT** 类只读查询；禁止 DROP/DELETE 除非用户明确要求且路径确认。
- 常用库：`memory.db`、`workflow.db`、`scheduler.db` 等（见 `/meta/doctor`）。
- 结果行数用 `limit` 控制；敏感列（token）勿回显到聊天。""",
    ),
    (
        "tool_mcp_invoke",
        "工具：mcp_invoke",
        "mcp_invoke,MCP 桥接,/mcp/call,外部工具",
        """- 先 `GET /mcp/status` 与 `/mcp/tools` 看已注册工具。
- `server` + `tool` + `arguments` 与 Cursor MCP 概念对齐；失败贴服务器返回错误。
- 不协助用 MCP 执行未授权远程控制或凭证窃取。""",
    ),
    (
        "feature_chat_memory",
        "能力：会话记忆与 FTS",
        "memories,记忆,consolidate,vault,会话搜索,preferences",
        """- API：`/chat/memories/*`、`/chat/sessions/search`、偏好 `/chat/preferences`。
- 写入前合并近似条目；引用记忆时标注可能过时。
- 导出：`/chat/memories/vault/export` 需用户知情同意。""",
    ),
    (
        "feature_scheduler",
        "能力：定时任务",
        "scheduler,定时,周期任务,cron,自动跑",
        """- API：`/scheduler/jobs` 列表/创建；`/jobs/{id}/run` 立即执行。
- 任务提示词应自包含；间隔 `interval_sec` 不宜过短以免刷爆 LLM。
- UI 面板「定时」与斜杠 `/scheduler` 可跳转。""",
    ),
    (
        "feature_gateway",
        "能力：网关入站",
        "gateway,telegram,inbound,webhook 入站",
        """- `GET /gateway/status`；`POST /gateway/inbound` / `telegram` 需配置与密钥。
- 不把用户 `.env` 密钥写入记忆或公开回复。""",
    ),
    (
        "feature_observe",
        "能力：Observe 态势简报",
        "observe,dashboard,简报,态势,/observe",
        """- `/observe/dashboard`、`/observe/report/today`：基于本机采样，**不虚构**全球实时情报。
- 与 `situational_intel_observe` 技能重复时以此 API 路径为准。""",
    ),
    (
        "feature_telegraf",
        "能力：Telegraf 指标导出",
        "telegraf,prometheus,metrics,快照,/telegraf",
        """- `/telegraf/prometheus` 文本、`/telegraf/snapshot` JSON。
- 讨论 SRE 时用真实端点片段；不编造未部署的 metric 名。""",
    ),
    (
        "feature_workflow",
        "能力：工作流与审查",
        "workflow,reviews,templates,dashboard,审查模板",
        """- `/workflow/reviews`、`/workflow/templates`、`/workflow/dashboard`。
- 编码交付流程可叠加 `creative_delivery_pipeline` 与 `spec_minimal_steps`。""",
    ),
    (
        "feature_orchestrator",
        "能力：Orchestrator 长任务",
        "orchestrate,task_id,长编排,/orchestrate",
        """- `POST /orchestrate` 提交；`GET /orchestrate/{task_id}` 轮询。
- 与 `run_task_orchestration` 工具互补：HTTP 异步 vs Agent 内同步编排。""",
    ),
    (
        "feature_evolution",
        "能力：进化蒸馏",
        "evolve,distill,进化,playbook,/agent/evolve",
        """- `POST /agent/evolve/distill`：从行为库提炼规则；`GET /agent/playbook` 查看。
- 蒸馏结果写入前让用户确认，避免错误偏好固化。""",
    ),
    (
        "npm_supply_chain_safety",
        "npm 供应链安全",
        "npm audit,供应链,依赖漏洞,typosquat,postinstall",
        """- 用 `run_project_check` target=frontend；建议用户本地 `npm audit`。
- 拒绝：恶意 postinstall、凭证回传、依赖投毒协助。
- 升级依赖时说明 breaking change 风险，不盲目 `@latest`。""",
    ),
    (
        "gaussian_splatting_creative",
        "3D 与高斯溅射创作",
        "gaussian splatting,3dgs,nerf,点云,三维重建",
        """- 只讨论合法资产、自有数据与开源工具链；不协助未授权模型/数据集爬取。
- 输出：管线阶段（采集→训练→导出→查看器）与验收（帧率、伪影、许可）。""",
    ),
    (
        "network_tunnel_legitimate",
        "合法网络隧道与加速",
        "hysteria,v2ray,wireguard,隧道,内网穿透",
        """- 仅限自建、企业授权或运营商合规场景；拒绝规避法律监管的具体操作教程。
- 故障排查：DNS、证书、防火墙、MTU；不提供「翻墙」类逐步规避指南。""",
    ),
    (
        "ai_growth_ethics",
        "AI 增长与变现伦理",
        "ai 赚钱,变现,增长黑客,刷量,affiliate",
        """- 可谈产品、定价、披露自动化边界；拒绝刷量、虚假宣传、未披露 bot 行为。
- 叠加 `trust_and_decline` 处理灰色营销请求。""",
    ),
    (
        "personal_local_super_agent",
        "本地超级智能体栈",
        "openhuman,本地超级代理,离线优先,private ai",
        """- 本机优先：`LLM_BACKEND=openai_compatible` + vLLM（`backend/.env.local-gemma4.example`）或 Ollama；云 API 须显式配置。
- 组合：`/agent/run` + `AGENT_SKILL_PACK=1` + `/meta/doctor` + 习惯体检；启动见 `START_APP_LOCAL.bat` / `START_VLLM_GEMMA4.bat`。
- 不把用户数据默认上传外网；拒绝依赖有 RPM/额度限制的云端为默认路径。""",
    ),
    (
        "memory_eval_consolidation",
        "记忆评测与合并",
        "agentmemory,记忆评测,去重,consolidate,benchmark memory",
        """- 写入 `/chat/memories` 前：查重、摘要、打时间戳。
- 用 `memories/consolidate` 与 `tree/rebuild` 维护结构；回答引用记忆时标「可能过时」。""",
    ),
    (
        "scientific_hypothesis_tables",
        "科学假设—证据表",
        "scientific skills,假设,证据表,反例,K-Dense",
        """- 输出表格：假设 | 证据 | 反例 | 置信度 | 下一步实验。
- 数值给区间与前提；单源不断言定论。
- 与 `academic_research_pipeline` 联用。""",
    ),
    (
        "claude_skills_domain_map",
        "Claude Skills 领域对照（本仓库落地）",
        "claude-skills,alirezarezvani,superpowers,mattpocock,领域技能",
        """外仓仅主题对照，正文在本地 `agent_skills`：

| 外仓常见域 | 本地技能 id |
|-----------|------------|
| 工程/代码库 | `codebase_context_first`, `spec_minimal_steps`, `tool_filesystem` |
| 科研 | `academic_research_pipeline`, `scientific_hypothesis_tables` |
| 编排 | `swarm_orchestration_lite`, `orchestration_handoff`, `tool_task_orchestration` |
| 安全 | `trust_and_decline`, `npm_supply_chain_safety` |
| 趋势 | `github_trending_developers`, `weekly_trend_map` |
| 工具 | `tool_*` 全系列 |

完整列表：`skills_master_index` + `GET /meta/skills`。""",
    ),
    (
        "onyx_frontend_react",
        "ONYX 前端 React",
        "frontend,react,App.js,OperatorPanels,侧栏",
        """- 路径 `frontend/src/`；构建 `npm run build`。
- Electron 资源用 `assetUrl()`（见 `BrandLogo.js`）；改 UI 保持现有 CSS 变量与侧栏结构。
- 技能面板读 `/meta/skills`，勿写死技能数量。""",
    ),
    (
        "onyx_electron_desktop",
        "ONYX Electron 桌面",
        "electron,main.js,桌面应用,shortcut,图标",
        """- `electron/main.js`：后端健康等待、`ensureOllama`。
- 快捷方式：`Launch-ONYX-OVERRIDE.vbs` + `scripts/create-desktop-shortcut.ps1`。
- 图标：`electron/icon.ico`、 branding 脚本 `scripts/build-branding.py`。""",
    ),
    (
        "onyx_ollama_ops",
        "ONYX Ollama 运维",
        "ollama,模型拉取,11434,LLM_BACKEND,起不来",
        """- `scripts/ensure-ollama.ps1`、`START_APP.bat` 自动拉起。
- `/meta/doctor` → `ollama_reachable`；`/meta/models` 列表。
- 连接失败中文提示见 `llm_client.py`；勿在未启动 Ollama 时声称模型可用。""",
    ),
    (
        "onyx_packaging_release",
        "ONYX 打包发布",
        "zip,打包,desktop zip,package,发布",
        """- `scripts/package-desktop-zip.ps1` → 桌面 `ONYX-OVERRIDE-v*.zip`。
- 排除 `node_modules`；含 `INSTALL_FIRST_RUN.bat` 与 README。
- 发版前：`npm run build` + `/meta/doctor` 通过。""",
    ),
    (
        "api_contract_design",
        "API 契约设计",
        "openapi,契约,错误码,版本,REST 设计",
        """- 先冻结请求/响应 schema 与错误码表，再实现 FastAPI 路由。
- 破坏性变更升版本或加兼容字段；文档与 `meta_routes` 对齐。""",
    ),
    (
        "fastapi_route_debug",
        "FastAPI 路由调试",
        "fastapi,uvicorn,422,路由,backend 调试",
        """- 路由分散在 `*_routes.py`；统一前缀见 `main.py`。
- 500 时贴 traceback 片段；用 `/meta/doctor` 查 DB 与 Ollama。""",
    ),
    (
        "sqlite_ops_playbook",
        "SQLite 运维剧本",
        "sqlite,wal,迁移,备份,behavior.db",
        """- 库文件在 `backend/*.db`；查询用 `query_database` 只读。
- 备份：复制文件前停写或 WAL checkpoint；不擅自 DELETE 用户数据。""",
    ),
    (
        "knowledge_vault_ingest",
        "Knowledge Vault 灌库",
        "knowledge-vault,memory_,灌库,本地知识库",
        """- 目录 `knowledge-vault/`；`local_search` 可检索。
- 新条目命名 `memory_*.md` 保持一致；索引见 `index.md`。""",
    ),
    (
        "chat_streaming_ux",
        "聊天流式与错误恢复",
        "stream,sse,聊天断了,流式,保存消息",
        """- `POST /chat/` 流式；失败时 backend 仍尝试保存 assistant 错误条。
- 前端 `sendAgent` 检查 `res.ok`；健康条来自 `/meta/doctor`。""",
    ),
    (
        "agent_forced_skill",
        "强制挂载技能语法",
        "[skill:,/skill,强制技能,指定技能",
        """- 前缀 `[skill:stem]` 或 UI `/skill stem` / 技能卡片。
- stem 与文件名一致（无 `.md`）；不存在则回退自动匹配。
- 例：`[skill:tool_http_request] 测试 GET /meta/info`""",
    ),
    (
        "slash_commands_operator",
        "斜杠命令操作员",
        "/doctor,/skills,/scheduler,/mode,/model,/tools,/help",
        """- `/doctor`：系统体检；`/skills` 开技能面板；`/skill <id>` 挂载。
- `/scheduler` 定时；`/mode chat|agent`；`/model <名>`；`/tools` 工具列表。
- 空状态 `/help` 列出以上命令。""",
    ),
    (
        "security_local_audit",
        "本地安全审计清单",
        "安全审计,secrets,.env,凭证,渗透",
        """- 扫描勿将 `.env`、token 提交或写入记忆；`run_project_check` + 人工 review。
- 拒绝未授权渗透、木马、凭证窃取；合法自查限于用户自有项目。""",
    ),
    (
        "docs_readme_changelog",
        "文档与 README",
        "readme,changelog,安装,INSTALL,首次运行",
        """- `README.md`、`INSTALL_FIRST_RUN.bat` 为入门权威。
- 改功能时同步 README 一节；版本与 zip 名一致（如 v1.1.0）。""",
    ),
    (
        "ruflo_style_swarm",
        "Ruflo 风格多 Agent",
        "ruflo,ruvnet,swarm,多 agent 编排",
        """- 对标 trending 的 ruflo 主题：用 `run_parallel_subagents` + `run_task_orchestration`。
- 技能链：`swarm_orchestration_lite` → `orchestration_handoff` → 本条。
- 合并策略写清「谁写盘」。""",
    ),
    (
        "plannotator_style_gate",
        "Plannotator 风格计划门",
        "plannotator,plan gate,先计划,审阅后再执行",
        """- 复杂改动：先输出计划 + 风险 + 回滚，用户确认后再 `write_file` / 浏览器操作。
- 细节见 `agent_plan_diff_review`；禁止跳过门控直接大改。""",
    ),
    (
        "codex_lb_routing",
        "Codex-LB 多账号路由",
        "codex-lb,多账号,负载均衡,openai_compatible",
        """- `LLM_BACKEND=openai_compatible` + `OPENAI_BASE_URL` + `EXTRA_MODEL_IDS`。
- `/meta/models` 合并 runtime 与 extra；轮换策略由用户网关实现，Agent 不存密钥。""",
    ),
    (
        "worldmonitor_observe",
        "WorldMonitor 风格观测",
        "worldmonitor,全球面板,新闻态势",
        """- 用 `/observe/*` 与本机采样；不编造实时战报或股价。
- 与 `situational_intel_observe` 一致：标注数据来源与延迟。""",
    ),
    (
        "stitch_mcp_ui",
        "Stitch MCP UI 交接",
        "stitch,stitch-mcp,设计稿,figma handoff",
        """- UI 任务走 `design_stitch_handoff`：布局、断点、验收截图再改 `frontend/src`。
- 无设计稿时先 wireframe 文字说明再实现。""",
    ),
    (
        "transcribe_whisper_local",
        "本地 Whisper 转写",
        "whisper,transcribe,speech_to_text,语音转文字",
        """- API：`POST` 本地 agent `speech_to_text`（见 `local_agent_api.py`）。
- 与 `local_transcription` 技能一致；大文件分片转写。""",
    ),
    (
        "git_wt_parallel",
        "Git Worktree 并行开发",
        "git worktree,git-wt,并行分支,多工作区",
        """- 详见 `git_worktree_workflow`；Agent 不 force push、不擅自改 git config。
- 并行任务：每 worktree 单写者。""",
    ),
    (
        "rlm_recursive_reasoning",
        "RLM 递归长文推理",
        "rlm,rlm-rs,递归推理,长上下文",
        """- 见 `recursive_long_document`：分块 → 并行摘要 → 合并 → 二次提问。
- 禁止声称已通读未加载的全文。""",
    ),
]


def main() -> None:
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    created = 0
    skipped = 0
    for stem, title, triggers, body in SKILLS:
        path = SKILL_DIR / f"{stem}.md"
        if path.exists():
            skipped += 1
            continue
        content = f"# {title}\n\nTriggers: {triggers}\n\n---\n\n{body.strip()}\n"
        path.write_text(content, encoding="utf-8")
        created += 1
    total = len(list(SKILL_DIR.glob("*.md")))
    print(f"created={created} skipped={skipped} total_md={total}")


if __name__ == "__main__":
    main()
