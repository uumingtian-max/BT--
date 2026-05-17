# 聊天流式与错误恢复

Triggers: stream,sse,聊天断了,流式,保存消息,chat_streaming_ux,chat streaming ux,chat-streaming-ux,聊天流式与错误恢复,聊天卡住,流式断了,没保存

---

**何时使用**：用户意图与「聊天流式与错误恢复」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. `POST /chat/` 流式；失败时 backend 仍尝试保存 assistant 错误条
2. 前端 `sendAgent` 检查 `res.ok`；健康条来自 `/meta/doctor`

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- API /meta/doctor

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「聊天流式与错误恢复」相关的事
- [skill:chat_streaming_ux] 执行一步可验证操作
