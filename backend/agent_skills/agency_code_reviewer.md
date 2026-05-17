# 代码审查（agency Code Reviewer）

Triggers: code review,代码审查,PR审查,review diff,agency_code_reviewer,agency code reviewer,审查代码,合并前检查,CR,agency-code-reviewer,agency,Code,Reviewer

---

**何时使用**：用户要审查改动、合并前把关，或 Triggers 命中时挂载。对标 [agency-agents](https://github.com/msitarzewski/agency-agents) `engineering-code-reviewer`。

## 执行步骤

1. 先读相关文件与 diff，对齐仓库风格
2. 按优先级列问题：**Blocker**（安全/数据/契约）→ **Should**（校验/测试/性能）→ **Nit**
3. 每条：位置 + 原因 + 具体改法；先摘要再列表
4. 点名做得好的模式；一轮给全量反馈
5. 能跑时用 `run_project_check` 或 `pytest`/`ruff` 佐证

## 避免

- 纠结无 linter 的格式偏好
- 无读取就声称已 review
- 把 `.env`、token 写入聊天

## ONYX 对接

- 工具：`read_file`、`run_project_check`
- 复杂多文件：可配合 `run_task_orchestration` 的审查子任务

## 自测用语

- 帮我 review 这次 backend 改动
- [skill:agency_code_reviewer] 列出必须修的安全项
