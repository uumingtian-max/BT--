# Agent Radar 2026 — BT（黑光）升级雷达

> 目的：收集闭源/开源 Agent 项目的共性能力，把能落地的部分转成 BT（黑光）的本地优先升级路线。本文不要求整仓复制外部项目，只吸收架构模式。

## 一句话结论

BT（黑光）不要做“又一个聊天框”。下一阶段要做成 **本地 Agent Control Plane**：任务可恢复、工具可审计、风险可确认、记忆可沉淀、执行可视化、模型可切换、手机端可远程查看。

## 标杆项目与可借鉴点

| 类型 | 项目/平台 | 强项 | BT 可落地点 |
| --- | --- | --- | --- |
| 开源框架 | LangGraph | long-running stateful agents、durable execution、human-in-the-loop、memory、event streaming | 把 `/agent/run` 和 `/automation/run` 的每一步写入持久 run graph；支持暂停、恢复、人工确认 |
| 开源/官方 SDK | OpenAI Agents SDK | agents as tools/handoffs、guardrails、sessions、tracing、sandbox agents、MCP | 增加 handoff/子 Agent 注册表；工具输入输出 guardrail；本地 sandbox workspace；trace 导出 |
| 开源/官方 SDK | Google ADK | graph workflows、multi-agent workflows、runtime、observability、evaluation、A2A、Ollama/vLLM 集成 | 强化 A2A 和 MCP；把自动化任务做成图工作流；增加评测与回放 |
| 开源框架 | CrewAI | crews + flows、状态流、事件驱动、工具/知识/记忆、企业观测 | 用“Flow 管流程，Crew 管专家”的思想重构 orchestrator：Planner、Coder、Reviewer、Operator |
| 开源框架 | AutoGen | 多 Agent 会话、Studio UI、Docker command line executor | 为复杂代码任务加 isolated executor 与对话式多 Agent 审查 |
| 闭源产品 | Devin / Cursor / Claude Code / Copilot Coding Agent | 项目级指令、分支/PR 工作流、日志、计划、差异审查、后台任务 | 根目录 `AGENTS.md`、任务计划面板、diff review、GitHub Sync Panel、执行日志归档 |
| 闭源平台 | ChatGPT Agent / Operator 类产品 | 浏览器/电脑操作、长期任务、用户确认、联网检索 | 浏览器自动化要分 safe/confirm/dangerous；所有外部动作进入事件流 |

## 能直接变成黑光功能的 10 个方向

1. **Run Graph 持久化**：每次 Agent/Automation 运行生成 run_id，步骤节点包含 thinking、tool_call、tool_result、artifact、error、final。
2. **可恢复任务**：失败后从最后成功节点继续，而不是整条任务重跑。
3. **人工确认闸门**：文件删除、系统命令、GitHub push、远程访问配置等进入 pending approval。
4. **工具 Guardrail**：每个工具都有参数 schema、风险等级、允许目录、输出裁剪、敏感信息过滤。
5. **Handoff 子 Agent**：Planner、Coder、Reviewer、Researcher、Operator、Memory Curator 分工明确。
6. **Sandbox Workspace**：复杂代码改动先在临时 workspace 或分支中跑，成功后再合并。
7. **Trace/Timeline UI**：前端展示事件流、工具耗时、错误、产物链接、重试按钮。
8. **模型岗位路由**：轻任务走小模型，规划/审查/复杂代码走专用模型，所有路由可视化。
9. **记忆压缩与技能沉淀**：成功任务自动总结为 playbook，写入 `backend/agent_skills/` 或知识树。
10. **Agent 雷达更新机制**：定期维护 `docs/AGENT_RADAR_2026.md` 和 `/meta/alignment`，但不整仓复制外部代码。

## 与当前项目现状对齐

已具备：

- FastAPI 后端、React/Electron 前端、本地 SQLite。
- `/meta/doctor`、`/meta/info`、`/meta/tools/registry`、`/automation/*`、`/meta/visual-events`。
- 工具风险分层、自动化运行记录、可视化事件流雏形。
- MCP、A2A、scheduler、memory、workflow、habit pipeline。
- `backend/agent_skills/*.md` 技能包体系。

明显缺口：

- 事件流目前偏内存态，重启后 visual events 丢失；应落 SQLite。
- 自动化任务还只是 allow-list 命令集合，未形成可编辑图工作流。
- Agent run 的每一步还没有统一 run graph 持久结构。
- 子 Agent/handoff 还没有统一注册表和 UI。
- Guardrail 需要从文档/工具注册表升级为执行前强校验。
- GitHub Sync、diff review、手机端二维码入口还需要更完整前端。

## 分阶段实施

### P0：安全和可观测底座

- 新增 `run_graph_store.py`：SQLite 表 `runs`、`run_steps`、`run_artifacts`。
- `visual_event_bus` 从纯内存改为“内存 + SQLite 最近事件”。
- `/meta/visual-events` 支持按 run_id/source/status 查询。
- 工具调用统一写入 run_step。

### P1：Agent Control Plane UI

- 前端新增或增强：`ToolTimeline`、`RunLogsPanel`、`ProjectHealthPanel`、`GitHubSyncPanel`。
- 自动化面板显示命令、耗时、exit code、日志裁剪、产物链接。
- `/automation/run` 支持 dry_run 与 rerun_failed。

### P2：Handoff 与专家 Agent

- 新增 `agent_roles.py`：Planner、Coder、Reviewer、Researcher、Operator、Memory Curator。
- Orchestrator 根据任务类型选择专家链路。
- 每个专家输出结构化结果，进入 trace。

### P3：Guardrails 与确认机制

- 工具注册表增加 `requires_confirmation`、`allowed_paths`、`redact_outputs`、`max_runtime_sec`。
- dangerous 工具必须带 confirmed token。
- 前端提供 pending approvals 列表。

### P4：记忆和技能自进化

- 成功任务自动写 `workflow_store` 复盘。
- 将高频成功步骤压缩成技能建议。
- 用户确认后写入 `backend/agent_skills/learned_*.md`。

## 不做什么

- 不把外部仓库整仓复制进主上下文。
- 不依赖单一云平台。
- 不让危险工具绕过确认。
- 不把用户数据库、日志、`.env` 推上 GitHub。
- 不把 BT 改成纯 LangGraph/CrewAI/ADK 项目；BT 保持本地优先，按需吸收模式。

## 维护规则

每次根据 Agent Radar 更新项目时：

1. 先看 `git status` / `git diff`。
2. 小步提交。
3. 跑对应测试或构建。
4. 在最终汇报里说明真实验证结果。
5. 文档引用要保守，避免宣传未落地能力。
