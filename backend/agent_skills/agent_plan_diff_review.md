# Agent 计划与 Diff 审阅（Plannotator 思路）

Triggers: plannotator,计划审阅,审查计划,review plan,diff review,方案评审,执行前先,backnotprop,annotate,agent_plan_diff_review,agent plan diff review,agent-plan-diff-review,Agent,计划与,Diff,审阅,思路,审查diff

---

**何时使用**：用户意图与「Agent 计划与 Diff 审阅（Plannotator 思路）」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. **计划阶段**：用条目列出目标、假设、将调用的工具（`web_search`/`write_file`/…）、预计产物路径；标「需用户确认」项
2. **禁止**：在计划未确认前调用 `write_file`、`execute_python`、浏览器自动化（除非用户明确「直接执行」）
3. **Diff 心智**：若涉及改代码，用 `read_file` 后只输出 unified 风格摘要（路径、增删意图），不编造未读到的行号
4. **一键反馈**：用户说「按意见改计划」时修订清单，而非偷偷执行
5. **与编排**：确认后可用 `run_task_orchestration`；审查者角色只出风险与测试建议

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `web_search`
- 工具/配置 `write_file`
- 工具/配置 `execute_python`
- 工具/配置 `read_file`
- 工具/配置 `run_task_orchestration`

## 关联技能
- `plannotator_style_gate`
- `spec_minimal_steps`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「Agent 计划与 Diff 审阅（Plannotator 思路）」相关的事
- [skill:agent_plan_diff_review] 执行一步可验证操作
