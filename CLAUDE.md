# BT（黑光）— Claude Code Agent Instructions

> 本文件供 Claude Code、Cursor、Windsurf、Copilot Workspace 等 AI 编程 Agent 读取。
> 在这个仓库里工作时，请严格遵守以下规则。

---

## 项目简介

BT（黑光）是一个**本地优先、持久记忆的 AI Agent 工作台**。核心理念：
- 每次会话的观察、技能、习惯都会写入持久存储，Agent 会随时间成长
- 所有工具调用均可视化（thinking → tool_call → tool_result → final_answer）
- 多模型智能路由：用对的模型做对的事，不浪费显存

**技术栈：** Python 3.10+ · FastAPI · React · Electron · Ollama / llama.cpp / vLLM

---

## 目录结构（必须了解）

```
backend/          FastAPI 后端，所有 Agent 逻辑在此
  model_router.py   任务→模型 路由层（修改模型分配从这里入手）
  llm_client.py     LLM transport（Ollama / OpenAI-compatible）
  agent.py          Agent 主循环
  memory_store.py   持久记忆读写
  skill_pack.py     技能包加载
  settings.py       Pydantic 配置（从 .env 读取）
  tests/            pytest 测试，改后端前先跑

frontend/         React 前端
  src/components/   Agent 时间线、工具面板、聊天气泡

skills/           可复用 Agent 技能（.md 格式，人类和 AI 均可读）
.cursor/rules/    Cursor 规则（MDC 格式）
```

---

## 编码规则

### Python（backend/）

- **类型注解必须**：所有函数参数和返回值加类型注解，`from __future__ import annotations`
- **异步优先**：I/O 操作用 `async/await`，不阻塞事件循环
- **不允许**：裸 `except:`、硬编码模型名（用 `model_router.get_model()`）、直接写 `os.environ.get("AGENT_DEFAULT_MODEL")` 绕过路由层
- **日志**：用 `logging.getLogger(__name__)`，不用 `print()`
- **测试**：修改 backend/ 任何文件后，确保 `pytest backend/tests/ -q` 全绿

### 模型路由（重要）

```python
# ✅ 正确：通过路由层选模型
from model_router import select_model, get_embed_model
model, reason = select_model(user_input, mode="chat")

# ❌ 错误：硬编码
model = "qwen3.5:9b"
model = os.environ.get("AGENT_DEFAULT_MODEL")
```

### 当前模型分配（5090 · Ollama 五模型栈示例）

| 任务 | 模型 | env key |
|------|------|---------|
| 向量嵌入 | nomic-embed-text | `EMBED_MODEL` |
| 工具路由 | functiongemma | `AGENT_ROUTER_MODEL` |
| 主聊天 / 快答 / 审查 | qwen3.5:9b | `AGENT_DEFAULT_MODEL` |
| 推理 / 规划 | deepseek-r1:7b | `REASONING_MODEL` |
| 复杂代码（按需）| deepseek-coder-v2:16b | `CODE_MODEL` |

### TypeScript / React（frontend/）

- 组件用函数式 + Hooks，不用 class component
- 事件流走 `EventSource`（SSE），不用轮询
- 新增 UI 状态放 `zustand` store，不散落在 props

---

## 新增功能流程

### 新增工具

1. 在 `backend/tools/` 新建 `your_tool.py`
2. 实现 `async def run(params: dict) -> dict` 接口
3. 在 `backend/tool_registry.py` 注册（name / description / risk_level / parameters schema）
4. 在 `backend/tests/` 添加对应测试
5. 更新 `skills/` 目录（如果工具对外有价值，写成 skill 文档）

### 新增 Agent 技能

1. 在 `skills/` 创建 `your-skill.md`（格式参考 `skills/habit-check.md`）
2. 在 `backend/skill_pack.py` 注册路径
3. 技能文件对人类和 AI 均可读，保持简洁

### 新增 API 端点

1. 在 `backend/` 新建 `your_routes.py`（FastAPI `APIRouter`）
2. 在 `backend/main.py` `include_router`
3. SSE 端点用 `EventSourceResponse`，普通 JSON 端点用 `JSONResponse`

---

## 禁止行为

- ❌ 不在 `backend/` 外直接写 SQLite（用 `memory_store.py` API）
- ❌ 不绕过 `safe_paths.py` 直接操作文件系统路径
- ❌ 不在前端 hardcode `localhost:8000`（用 `VITE_BACKEND_URL` env）
- ❌ 不删除 `.cursor/rules/` 里的规则文件
- ❌ 不在同一 commit 里同时改 backend/ 和 frontend/（除非是联动接口变更）

---

## CI / 质量门控

```bash
# 每次改动后本地验证
pytest backend/tests/ -q                    # 后端测试
ruff check backend/ && ruff format --check backend/   # lint + format
npm run build --prefix frontend              # 前端构建
```

CI 在 `.github/workflows/ci.yml` 定义，push/PR 自动触发。

---

## 关键 env 变量（`backend/.env`）

| 变量 | 说明 |
|------|------|
| `LLM_BACKEND` | `ollama` 或 `openai_compatible` |
| `OLLAMA_HOST` | Ollama 地址（默认 `http://127.0.0.1:11434`）|
| `SMART_ROUTER_ENABLED` | `1` = 开启智能路由（默认）|
| `HABIT_CHECK_ENABLED` | `true` = 每日习惯体检 |
| `TTS_ENABLED` | `false`（F5-TTS 可选）|

完整列表见 `backend/.env.example`。

---

*本文件遵循 [mattpocock/skills](https://github.com/mattpocock/skills) 约定的 CLAUDE.md 格式。*
