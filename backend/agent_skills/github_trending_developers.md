# GitHub Trending Developers 主题索引（2026-05）

Triggers: trending developers,github trending,今日开发者,热榜开发者,ruvnet,garrytan,plannotator,ruflo,gstack,rlm,a2a,worldmonitor,stitch,codex-lb,alirezarezvani

当用户提到 [GitHub Trending Developers](https://github.com/trending/developers) 或「按今日开发者热点升级」时，用**主题 → 本仓库能力**映射回答，不克隆外仓、不粘贴他人仓库正文。

| 热点方向 | 代表项目/作者 | 本仓库对齐 |
|---------|--------------|-----------|
| 多账号/负载 LLM 路由 | codex-lb | `LLM_BACKEND=openai_compatible` + `EXTRA_MODEL_IDS`；网关见 `gateway_routes` |
| Git 并行工作区 | git-wt | Agent 读写前 `list_files`/`read_file`；提醒用 worktree 避免脏工作区 |
| 超长文档推理 | rlm-rs | 技能 `recursive_long_document`；`local_search`+分块摘要，勿一次塞满上下文 |
| Agent 计划审阅 | plannotator | 技能 `agent_plan_diff_review`；复杂任务先清单再 `run_task_orchestration` |
| 多 Agent 编排 | ruflo | `run_task_orchestration`、`run_parallel_subagents` + `swarm_orchestration_lite` |
| Claude 式角色工具链 | gstack | 技能 `gstack_agent_roles`；规划/实现/审查/发布分工 |
| 技能目录生态 | claude-skills | `GET /meta/skills` + `backend/agent_skills/*.md` |
| 设计稿进开发 | stitch-mcp | 技能 `design_stitch_handoff`；UI 任务先冻结布局与验收 |
| 全球态势面板 | worldmonitor | `/observe/dashboard`、简报 API；不虚构实时情报 |
| Agent 互操作 | A2A | `/a2a/v1/agent-card`、`message:send` |
| 语音转写 | transcribe-anything | 本地 Whisper/Ollama  speech 模型；`text_to_speech` 为反向 |
| 包安全 | npm-security-best-practices | `npm_supply_chain_safety` + `run_project_check` target=frontend |
| 技能目录规模 | claude-skills / alirezarezvani | **86** 条本地技能：`GET /meta/skills` · 总索引 `skills_master_index` |

**执行原则**：先匹配用户目标 → 挂载上表对应技能 → 再调工具；高风险走 `trust_and_decline`。

**工具/API 专精**：`tool_*`（每个 Agent 工具）、`feature_*`（记忆/定时/网关/观测等）、`onyx_*`（本应用工程）— 见 `skills_master_index`。
