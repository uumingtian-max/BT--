# Codex-LB 多账号路由

Triggers: codex-lb,多账号,负载均衡,openai_compatible,codex_lb_routing,codex lb routing,codex-lb-routing,多账号路由,多key,api轮换

---

**何时使用**：用户意图与「Codex-LB 多账号路由」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. `LLM_BACKEND=openai_compatible` + `OPENAI_BASE_URL` + `EXTRA_MODEL_IDS`
2. `/meta/models` 合并 runtime 与 extra；轮换策略由用户网关实现，Agent 不存密钥

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- API /meta/models

## 关联技能
- `multi_provider_llm_routing`
- `onyx_ollama_ops`

## 自测用语（习惯体检 / 人工抽检）
- （自然语）帮我处理「Codex-LB 多账号路由」相关的事
- [skill:codex_lb_routing] 执行一步可验证操作
