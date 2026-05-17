# 多提供商 / 多账号 LLM 路由

Triggers: codex-lb,load balancer,多账号,openai compatible,9router,nim,路由,切换模型,负载,Soju06

对标 **codex-lb** 等：多上游、计量、故障转移 — 本仓库用配置实现，不内置账号池服务。

**配置路径**（只指导，不代改用户云账号）：

```env
LLM_BACKEND=openai_compatible
OPENAI_BASE_URL=http://127.0.0.1:20128/v1   # 9router / LiteLLM / 自建
OPENAI_API_KEY=...
AGENT_DEFAULT_MODEL=...
EXTRA_MODEL_IDS=model-a,model-b
```

**行为**：

1. `GET /meta/models` 合并 Ollama tags + `EXTRA_MODEL_IDS`。
2. Agent `call_llm` 已有模型 fallback 链；用户可在 UI 下拉切换。
3. 路由失败时：明确是 **连接** / **404 模型名** / **鉴权** 三类，对应 `llm_client` 中文错误。
4. 不协助：绕过付费配额、共享盗版 API、违反 ToS 的账号轮转。

聊天与 Agent 共用 `.env`；改配置后需重启后端。
