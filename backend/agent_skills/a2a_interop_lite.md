# A2A 互操作（Agent2Agent 轻量）

Triggers: a2a,agent2agent,agent card,message:send,互操作,holtskinner,跨agent,agent-card

本仓库已暴露 A2A 风格端点（见 `a2a_bridge`）：

- `GET /a2a/v1/agent-card` — 能力卡片
- `POST /a2a/v1/message:send` — 单轮消息 → 内部 `run_agent`

**回答用户时**：

1. 说明这是**本机 shim**，非完整 A2A 集群实现；外部 Agent 需能访问 `127.0.0.1:8000`。
2. 集成步骤：先拉 agent-card → 再 POST 文本 → 解析 SSE/JSON 响应中的最终答案与工具轨迹摘要。
3. 与桌面 UI 并行时：避免双写同一 `memory.db`；长任务优先走 Agent 模式并限步数。
4. 不要承诺与 Google ADK / 云端 Registry 自动发现互通，除非用户自行配置反向代理与鉴权。

故障：若 8000 未启动，先 `START_APP.bat`；Ollama 未就绪则卡片可返回但推理失败。
