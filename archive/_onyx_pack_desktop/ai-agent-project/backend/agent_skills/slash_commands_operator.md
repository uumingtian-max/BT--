# 斜杠命令操作员

Triggers: /doctor,/skills,/scheduler,/mode,/model,/tools,/help,slash_commands_operator,slash commands operator,slash-commands-operator,斜杠命令操作员,斜杠命令,命令列表

---

**何时使用**：用户意图与「斜杠命令操作员」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. `/doctor`：系统体检；`/skills` 开技能面板；`/skill <id>` 挂载
2. `/scheduler` 定时；`/mode chat|agent`；`/model <名>`；`/tools` 工具列表
3. 空状态 `/help` 列出以上命令

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `/doctor` `/skills` `/habit` `/scheduler` `/mode` `/model` `/tools`

## 自测用语（习惯体检 / 人工抽检）
- 有哪些斜杠命令
- /doctor 干什么
