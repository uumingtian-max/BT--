# 工具：run_task_orchestration

Triggers: run_task_orchestration,编排,多步任务,子任务分解,tool_task_orchestration,tool task orchestration,tool-task-orchestration,task orchestration,工具,分步骤,多步完成,拆解任务,工具task orchestration,一条龙,task_orchestration

---

**何时使用**：用户需要 **多步子任务编排**（工具 `task_orchestration`）或口语里出现搜索/读写/执行/浏览器/HTTP 等同义场景时，**应优先**挂载本技能再调工具，避免无 playbook 裸调。

## 执行步骤
1. 复杂目标先拆 3–7 步，每步有可验证产物（文件/命令输出/HTTP 状态）
2. 与 `agent_plan_diff_review` 联用：高风险步骤先出计划再执行
3. 单写者原则：并行子任务勿同时改同一文件（见 `swarm_orchestration_lite`）

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `agent_plan_diff_review`
- 工具/配置 `swarm_orchestration_lite`

## 关联技能
- `orchestration_handoff`
- `agent_plan_diff_review`
- `swarm_orchestration_lite`
- `tool_reliability`
- `trust_and_decline`

## 自测用语（习惯体检 / 人工抽检）
- 用task orchestration帮我做一件可验证的小事
- [skill:tool_task_orchestration] 调用工具并给出证据
