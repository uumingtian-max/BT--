# Agent 雷达 / 黑光升级路线（2026）

> 对标 LangGraph、OpenAI Agents SDK、Google ADK、CrewAI 等的能力抽象，不照搬实现。

## 标杆强项（摘要）

| 方向 | 标杆 | 可借鉴点 |
| --- | --- | --- |
| 可恢复执行 | LangGraph | checkpoint、run 状态机 |
| Trace / 时间线 | OpenAI Agents、Devin | run_steps、artifacts |
| Handoff / 编排 | OpenAI Agents、ADK | 多 Agent 路由（已有 orchestrator） |
| Guardrails | OpenAI Agents | policy_guard、confirm 工具 |
| 企业触发 | CrewAI | scheduler + automation jobs |

## 黑光已落地（P0）

- **Run Graph SQLite**：`backend/run_graph_store.py`
  - 表：`runs`、`run_steps`、`run_artifacts`、`visual_events`
  - 自动化：`automation_runner` 写入步骤；`visual_event_bus` 事件落库
  - API：`GET /meta/run-graph/runs/{id}`、`GET /automation/runs/{id}/graph`

## 建议下一刀（P1）

- Agent `/agent/run` 同步写入 run_graph（与 automation 同一套时间线）
- 前端工作台：按 `run_id` 拉 steps 时间轴
- 可选：SSE 推送 `visual_events` 新行

## 技能

本地 Agent 加载：`backend/agent_skills/agent_radar_2026.md`（若仓库内存在）。
