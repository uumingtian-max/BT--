# 多提供商 / 多账号 LLM 路由

Triggers: codex-lb,load balancer,多账号,openai compatible,9router,nim,路由,切换模型,负载,Soju06,multi_provider_llm_routing,multi provider llm routing,multi-provider-llm-routing,多提供商,LLM,换模型,openai兼容,integrate

---

**何时使用**：用户意图与「多提供商 / 多账号 LLM 路由」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. `GET /meta/models` 合并 Ollama tags + `EXTRA_MODEL_IDS`
2. Agent `call_llm` 已有模型 fallback 链；用户可在 UI 下拉切换
3. 路由失败时：明确是 **连接** / **404 模型名** / **鉴权** 三类，对应 `llm_client` 中文错误
4. 不协助：绕过付费配额、共享盗版 API、违反 ToS 的账号轮转

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 工具/配置 `call_llm`
- 工具/配置 `llm_client`

## 自测用语（习惯体检 / 人工抽检）
- 怎么接 9router
- OPENAI_BASE_URL 怎么配
