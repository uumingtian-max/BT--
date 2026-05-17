# 能力：Orchestrator 长任务

Triggers: orchestrate,task_id,长编排,/orchestrate,feature_orchestrator,feature orchestrator,feature-orchestrator,orchestrator,能力,长任务,提交长任务,异步编排

---

**何时使用**：用户涉及 ONYX **HTTP 长编排**（`feature_orchestrator`）或相关 API/面板/斜杠命令时**应**挂载；系统体检 `/meta/doctor` 失败也可附带本技能。

## 执行步骤
1. `POST /orchestrate` 提交；`GET /orchestrate/{task_id}` 轮询
2. 与 `run_task_orchestration` 工具互补：HTTP 异步 vs Agent 内同步编排

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `POST /orchestrate` · `GET /orchestrate/{task_id}`

## 关联技能
- `skills_master_index`

## 自测用语（习惯体检 / 人工抽检）
- 查一下orchestrator功能状态
- [skill:feature_orchestrator] 走对应 API 试一步
