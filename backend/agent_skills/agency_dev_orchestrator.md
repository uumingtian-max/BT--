# 开发流水线编排（agency Orchestrator）

Triggers: 全流程,流水线,编排,多角色,dev qa loop,agency_dev_orchestrator,agency dev orchestrator,从需求到上线,任务编排,orchestrator,agency-dev-orchestrator,开发流水线编排,agency

---

**何时使用**：跨多步骤/多文件的大任务；与 `orchestration_handoff`、`gstack_agent_roles` 一起用。来源 agency-agents `agents-orchestrator`，落地为 BT 工具链。

## 执行步骤

1. **范围**：5 条内目标 + 不做清单
2. **拆解**：`spec_minimal_steps`；必要时 `run_task_orchestration`
3. **实现**：读代码 → 最小 diff；前端改动后项目根 `npm run build --prefix frontend`
4. **单任务 QA**：`run_project_check` / `pytest`；FAIL 则带错误摘要重试（≤3 次）
5. **门禁**：挂载 `agency_reality_checker` 思维；默认 NEEDS WORK
6. **交接**：假设、已完成、阻塞、下一步最小动作（勿整段日志甩给下一角色）

## 避免

- 子任务未验证就标整体完成
- 跳过审查直接「已上线」

## ONYX 对接

- `run_task_orchestration` · `orchestration_handoff` · `gstack_agent_roles`

## 自测用语

- [skill:agency_dev_orchestrator] 把「加 CI + 修路由」拆成可验证步骤
- 多文件重构：经理→实现→审查三拍
