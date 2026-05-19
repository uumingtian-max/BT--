# 架构说明

ONYX-OVERRIDE 是一个本地优先的桌面 AI Agent 项目，主要由 Electron 桌面壳、React 前端、FastAPI 后端和本地/兼容 LLM 后端组成。

## 运行链路

```text
用户
  ↓
Electron 桌面壳
  ↓
React 前端
  ↓
FastAPI Backend
  ├─ /chat          普通聊天与 SSE 输出
  ├─ /agent/run     Agent 执行与工具调用
  ├─ /agent/tools   工具清单
  ├─ /meta/*        运行时、模型、技能、自检
  ├─ /scheduler/*   定时任务
  └─ /observe/*     本地观察与画像
  ↓
LLM Backend
  ├─ Ollama
  └─ OpenAI-compatible gateway，例如 vLLM / NIM / LiteLLM
```

## 后端模块职责

| 模块 | 职责 |
| --- | --- |
| `backend/main.py` | FastAPI 应用入口、生命周期任务、路由挂载、CORS、移动访问保护 |
| `backend/agent.py` | Agent 主循环、工具选择、工具执行、最终回答质量兜底 |
| `backend/agent_runtime.py` | 运行时配置、模型配置、Agent 限制项 |
| `backend/env_bootstrap.py` | 加载 `backend/.env`、日志配置、端口读取 |
| `backend/meta_routes.py` | 模型、技能、自检、运行时元信息 |
| `backend/scheduler_*` | 定时任务存储与后台执行 |
| `backend/observe.py` | 本地观察、窗口/进程画像、行为摘要 |
| `backend/tools/` | Agent 可调用工具实现 |
| `backend/agent_skills/` | Markdown 技能包，按触发词注入上下文 |

## 前端职责

| 目录 | 职责 |
| --- | --- |
| `frontend/src/` | React 应用源码 |
| `frontend/package.json` | Vite 构建与开发命令 |
| `electron/main.js` | Electron 主进程入口 |
| `assets/branding/` | 品牌图标与视觉资源 |

## Agent 执行流程

```text
1. 前端提交用户消息到 POST /agent/run
2. 后端保存用户轮次与记忆
3. 后端构建系统提示词、历史上下文、技能上下文、画像上下文
4. Agent 判断是否可以直接推断工具
5. 若需要工具：
   - 解析 tool_call
   - 执行 TOOL_MAP 中的函数
   - 压缩工具结果
   - 记录工具结果与任务结果
6. 基于真实工具结果生成最终回答
7. SSE 返回 thinking / tool_call / tool_result / final_answer
```

## 配置优先级

启动器和后端都应该读取 `backend/.env`。关键项：

```env
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
LLM_BACKEND=ollama
OLLAMA_HOST=http://127.0.0.1:11434
AGENT_DEFAULT_MODEL=qwen3.5:4b
```

维护规则：

1. 所有新配置先写入 `backend/.env.example`。
2. 后端读取配置统一走 `env_bootstrap.py` 或 `agent_runtime.py`。
3. 不要把真实密钥写入仓库。
4. 新增 API 后同步更新 README 和相关 docs。

## 后续建议

- 将 `backend/agent.py` 中的工具元数据拆到独立 `tool_registry.py`。
- 给危险工具增加 `risk_level` 和用户确认机制。
- 将 Agent 执行事件统一成结构化 schema，方便前端展示时间线。
- 给 `/agent/tools` 返回更丰富的工具描述、参数 schema 和风险等级。
