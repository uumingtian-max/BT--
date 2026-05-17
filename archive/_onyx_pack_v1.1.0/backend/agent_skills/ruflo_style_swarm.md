# Ruflo 风格多 Agent

Triggers: ruflo,ruvnet,swarm,多 agent 编排,ruflo_style_swarm,ruflo style swarm,ruflo-style-swarm,风格多,Agent

---

**何时使用**：用户意图与「Ruflo 风格多 Agent」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 对标 trending 的 ruflo 主题：用 `run_parallel_subagents` + `run_task_orchestration`
2. 技能链：`swarm_orchestration_lite` → `orchestration_handoff` → 本条
3. 合并策略写清「谁写盘」

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `run_parallel_subagents`
- 工具/配置 `run_task_orchestration`
- 工具/配置 `swarm_orchestration_lite`
- 工具/配置 `orchestration_handoff`

## 关联技能
- `swarm_orchestration_lite`
- `tool_parallel_subagents`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「Ruflo 风格多 Agent」相关的事
- [skill:ruflo_style_swarm] 执行一步可验证操作
