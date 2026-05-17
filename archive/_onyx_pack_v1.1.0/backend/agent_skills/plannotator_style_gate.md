# Plannotator 风格计划门

Triggers: plannotator,plan gate,先计划,审阅后再执行,plannotator_style_gate,plannotator style gate,plannotator-style-gate,风格计划门,先别改,先给方案,计划确认,先审阅

---

**何时使用**：高风险改动（删库、批量替换、发布）**必须**先计划门控。

## 执行步骤
1. 复杂改动：先输出计划 + 风险 + 回滚，用户确认后再 `write_file` / 浏览器操作
2. 细节见 `agent_plan_diff_review`；禁止跳过门控直接大改

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `write_file`
- 工具/配置 `agent_plan_diff_review`

## 关联技能
- `agent_plan_diff_review`
- `spec_minimal_steps`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「Plannotator 风格计划门」相关的事
- [skill:plannotator_style_gate] 执行一步可验证操作
