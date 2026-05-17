# RLM 递归长文推理

Triggers: rlm,rlm-rs,递归推理,长上下文,rlm_recursive_reasoning,rlm recursive reasoning,rlm-recursive-reasoning,递归长文推理

---

**何时使用**：用户意图与「RLM 递归长文推理」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. 见 `recursive_long_document`：分块 → 并行摘要 → 合并 → 二次提问
2. 禁止声称已通读未加载的全文

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `recursive_long_document`

## 关联技能
- `recursive_long_document`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「RLM 递归长文推理」相关的事
- [skill:rlm_recursive_reasoning] 执行一步可验证操作
