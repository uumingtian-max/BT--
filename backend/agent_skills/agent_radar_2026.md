# Agent 雷达与黑光升级路线（2026）

Triggers: Agent 雷达,agent radar,对标,LangGraph,OpenAI Agents,ADK,CrewAI,升级路线,run graph,时间线,tracing,黑光升级,agent_radar_2026

---

**何时使用**：用户要参考闭源/开源 Agent 项目给黑光排升级、或问「对标 Devin/Cursor/LangGraph 我们该补什么」。

## 执行步骤

1. 先读 `docs/AGENT_RADAR_2026.md` 里的能力矩阵与 P0/P1。
2. **已落地**：Run Graph（`run_graph_store.py`）— 自动化 run 有 steps/artifacts，事件进 SQLite。
3. 给建议时优先 **可验证小步**（API 已有、测试能跑），不要空喊「世界级」。
4. 涉及视频：区分 Omni **理解** vs `generate_video` **生成**（见 `nemotron_omni_multimodal.md`）。

## 避免

- 未读 `docs/AGENT_RADAR_2026.md` 就列一长串抄竞品功能。
- 提议改动 `backend/.env`、密钥、或绕过 `safe_paths` 的文件操作。

## 自测用语

- 参考 Agent 项目，黑光下一刀该做什么？
- 自动化 run 的时间线 API 在哪？
