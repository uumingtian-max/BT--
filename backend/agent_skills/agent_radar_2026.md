# Agent Radar 2026 升级参照

Triggers: Agent Radar,agent radar,闭源Agent,开源Agent,Agent项目,LangGraph,CrewAI,AutoGen,OpenAI Agents SDK,Google ADK,Devin,Cursor,Claude Code,Copilot Coding Agent,对标Agent,更新黑光Agent

---

**何时使用**：用户让你“收一下闭源开源 Agent 项目”“参考别人的 Agent 给黑光升级”“看看 LangGraph/CrewAI/AutoGen/OpenAI Agents/ADK 怎么借鉴”时加载。

## 核心判断

BT（黑光）不要照搬某个框架；目标是吸收共性模式，继续保持本地优先：

- 可恢复执行
- 可视化 trace/timeline
- 工具风险分层和确认
- 子 Agent handoff
- 本地记忆和技能沉淀
- MCP/A2A/OpenAI-compatible/Ollama 互操作

## 参考模式

1. **LangGraph**：持久状态、长任务、human-in-the-loop、事件流。
2. **OpenAI Agents SDK**：agents as tools、handoffs、guardrails、sessions、tracing、sandbox、MCP。
3. **Google ADK**：图工作流、上下文管理、A2A、多模型部署和评测。
4. **CrewAI**：crews/flows、触发器、知识/记忆/观测。
5. **AutoGen**：多 Agent 会话、Studio 可视化、Docker command executor。
6. **Devin/Cursor/Claude Code/Copilot**：项目级指令、分支/PR、diff review、计划、日志和产物。

## 落到 BT 的优先级

### P0

- `run_graph_store.py`：runs / run_steps / run_artifacts。
- `visual_event_bus`：从纯内存升级为 SQLite + 内存缓存。
- 所有 `/agent/run`、`/automation/run` 步骤都写 trace。

### P1

- 前端补 `ToolTimeline`、`RunLogsPanel`、`ProjectHealthPanel`、`GitHubSyncPanel`。
- 自动化面板支持 rerun、dry-run、日志展开。

### P2

- `agent_roles.py`：Planner、Coder、Reviewer、Researcher、Operator、Memory Curator。
- Orchestrator 做 handoff，不让一个 prompt 扛所有任务。

### P3

- 工具注册表补 `requires_confirmation`、`allowed_paths`、`max_runtime_sec`、`redact_outputs`。
- dangerous 工具必须确认，所有确认写入审计日志。

### P4

- 成功任务自动复盘成 playbook。
- 用户确认后写入 `backend/agent_skills/learned_*.md`。

## 使用方式

- 查完整路线：`docs/AGENT_RADAR_2026.md`
- 查当前实现状态：`/meta/doctor`、`/meta/operator-dashboard`、`/meta/visual-events`、`/automation/runs`
- 改代码前先 `git status` / `git diff`
- 改完必须跑最小真实验证

## 避免

- 不要整仓复制外部项目。
- 不要宣称未落地能力已经完成。
- 不要提交 `.env`、数据库、outputs、logs、frontend/build。
- 不要绕过危险工具确认。
