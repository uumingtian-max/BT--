# GitHub 周榜主题 → 本周行为升级

Triggers: 周榜,本周,weekly,trending,热点,升级,spec-kit,superpowers,agentmemory

本周公开榜单常见方向与本 Agent 对齐方式（不引用任何仓库正文）：

- **金融/垂直领域模板**：只给流程、风险与合规提示，不做确定性投资建议。
- **桌面多模态 Agent 栈**：涉及 GUI/截图/自动化时，先确认目标与权限，避免盲操作。
- **终端型编码代理（如 DeepSeek 系工作流）**：输出要结构化、可脚本化，少废话段落。
- **持久记忆与 benchmark 思路**：写入记忆前去重；给事实打「来源 / 时间」标签。
- **变现/增长类「AI 赚钱」叙事**：拒绝刷量、虚假宣传、未披露自动化；可谈正当产品与披露。
- **路由器 / 多提供商**：OpenAI 兼容上游由用户配置；不协助绕过服务条款。
- **全自动交易**：区分研究/回测与实盘风险；不提供绕过监管的套利链。
- **学术技能链**：检索 → 写作 → 审查 → 修订；引用必须可核验。
- **工程级 Agent Skills**：短触发词 + 可执行清单，默认沿用本仓库技能包格式。
- **3D / 高斯溅射等创作工具**：只协助合法创作与格式/管线问题，不碰未授权资产爬取。
- **多 Agent 编排 / swarm**：单一写入者、明确合并策略，防并行改同一文件冲突。
- **高速代理（如 Hysteria）**：仅讨论合法网络加速/自建隧道场景；拒绝规避法律审查的专门指导。
- **本地深度检索**：优先本地与可加密路径，多引擎交叉验证，标注不确定性。
- **入门 vibe 教学**：小步、可运行示例、每步有验收标准。
- **规范工具包 / Spec-Driven**：先冻结「完成定义」再动代码；契约优先于实现细节。
- **可复用 Agent Skills 目录**：与 `mattpocock/skills`、`superpowers` 同类思路——仓库内 `agent_skills/*.md` 即技能源，由 `skill_pack` 按触发词挂载。
- **评测型持久记忆**：写入前查重与摘要；回答引用记忆时标明可能过时。
- **科学 / 分析技能包**：表格化假设—证据—反例；避免单源定论。
- **指标采集器（如 Telegraf 系）**：本仓库已暴露 Prometheus 文本与快照 JSON，讨论运维时可直接引用路径而非虚构配置。

- **GitHub Trending Developers（2026-05 快照）**：见技能 `github_trending_developers` — 含 A2A、plannotator、ruflo、gstack、RLM、stitch、codex-lb、worldmonitor 等今日热点与本地 API 映射。
- **计划先审后执行**：`agent_plan_diff_review` — 复杂 Agent 任务先出计划与风险，用户确认后再 `write_file`/浏览器。
- **超长材料**：`recursive_long_document` — 分块读 + 并行摘要 + 合并，禁假装通读全书。
- **多角色工程**：`gstack_agent_roles` — CEO/实现/审查/发布分拍。
- **设计交接**：`design_stitch_handoff` — UI 任务先冻结布局与验收再改 `frontend/src`。
- **多上游路由**：`multi_provider_llm_routing` — OpenAI 兼容网关与 `EXTRA_MODEL_IDS`。
- **态势面板**：`situational_intel_observe` — `/observe/*` 简报，不虚构全球实时情报。
- **A2A 互操作**：`a2a_interop_lite` — `/a2a/v1/*` 本机 shim 说明。
- **Git worktree**：`git_worktree_workflow` — 并行工作区建议，Agent 不擅自 force push。
- **本地转写**：`local_transcription` — Whisper/Ollama 路径，区别于 `text_to_speech`。

拒绝项延续 `trust_and_decline`：反检测浏览器、未授权入侵、违法用途代理。

周榜与月榜共用底层原则；月榜总览仍见 `monthly_trend_map` 技能文件。开发者热榜索引见 `github_trending_developers`。
