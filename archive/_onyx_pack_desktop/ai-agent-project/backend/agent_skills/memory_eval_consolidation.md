# 记忆评测与合并

Triggers: agentmemory,记忆评测,去重,consolidate,benchmark memory,memory_eval_consolidation,memory eval consolidation,memory-eval-consolidation,记忆评测与合并,记忆重复,合并记忆,记忆太乱

---

**何时使用**：用户意图与「记忆评测与合并」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 写入 `/chat/memories` 前：查重、摘要、打时间戳
2. 用 `memories/consolidate` 与 `tree/rebuild` 维护结构；回答引用记忆时标「可能过时」

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- API /chat/memories

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「记忆评测与合并」相关的事
- [skill:memory_eval_consolidation] 执行一步可验证操作
