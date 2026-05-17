# Agent 计划与 Diff 审阅（Plannotator 思路）

Triggers: plannotator,计划审阅,审查计划,review plan,diff review,方案评审,执行前先,backnotprop,annotate

Inspired by trending **plan/diff review before execution** — 不自动改仓库，先让人/Agent 看清将做什么。

**流程（复杂 Agent 任务必走）**：

1. **计划阶段**：用条目列出目标、假设、将调用的工具（`web_search`/`write_file`/…）、预计产物路径；标「需用户确认」项。
2. **禁止**：在计划未确认前调用 `write_file`、`execute_python`、浏览器自动化（除非用户明确「直接执行」）。
3. **Diff 心智**：若涉及改代码，用 `read_file` 后只输出 unified 风格摘要（路径、增删意图），不编造未读到的行号。
4. **一键反馈**：用户说「按意见改计划」时修订清单，而非偷偷执行。
5. **与编排**：确认后可用 `run_task_orchestration`；审查者角色只出风险与测试建议。

输出模板：`## 计划` / `## 风险` / `## 建议测试` / `## 待确认`。
