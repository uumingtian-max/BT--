# A2A 互操作（Agent2Agent 轻量）

Triggers: a2a,agent2agent,agent card,message:send,互操作,holtskinner,跨agent,agent-card,a2a_interop_lite,a2a interop lite,a2a-interop-lite,轻量,对外agent

---

**何时使用**：用户意图与「A2A 互操作（Agent2Agent 轻量）」相关，或 Triggers 中任一词命中时**应**挂载；勿等待用户说出技能 id。

## 执行步骤
1. `GET /a2a/v1/agent-card` — 能力卡片
2. `POST /a2a/v1/message:send` — 单轮消息 → 内部 `run_agent`
3. 说明这是**本机 shim**，非完整 A2A 集群实现；外部 Agent 需能访问 `127.0.0.1:8000`
4. 集成步骤：先拉 agent-card → 再 POST 文本 → 解析 SSE/JSON 响应中的最终答案与工具轨迹摘要
5. 与桌面 UI 并行时：避免双写同一 `memory.db`；长任务优先走 Agent 模式并限步数
6. 不要承诺与 Google ADK / 云端 Registry 自动发现互通，除非用户自行配置反向代理与鉴权

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `GET /a2a/v1/agent-card` · `POST /a2a/v1/message:send`

## 自测用语（习惯体检 / 人工抽检）
- 拉一下 agent-card
- 用 A2A 发一条消息给本机 agent
