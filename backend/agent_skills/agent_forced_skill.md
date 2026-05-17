# 强制挂载技能语法

Triggers: [skill:,/skill,强制技能,指定技能,agent_forced_skill,agent forced skill,agent-forced-skill,强制挂载技能语法,用这个技能

---

**何时使用**：用户意图与「强制挂载技能语法」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 前缀 `[skill:stem]` 或 UI `/skill stem` / 技能卡片
2. stem 与文件名一致（无 `.md`）；不存在则回退自动匹配
3. 例：`[skill:tool_http_request] 测试 GET /meta/info`

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 前缀 `[skill:stem]` · UI `/skill <id>`

## 自测用语（习惯体检 / 人工抽检）
- 用 tool_http_request 技能测接口
- [skill:spec_minimal_steps] 拆任务
