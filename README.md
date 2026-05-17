# BKLT 黑光 / BLACKLIGHT

<div align="center">

**本地 AI Agent 自动化工作台 · Local AI Agent Automation Workbench**

[![CI](https://github.com/uumingtian-max/ai-agent-project/actions/workflows/ci.yml/badge.svg)](https://github.com/uumingtian-max/ai-agent-project/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Node](https://img.shields.io/badge/Node.js-18%2B-green?logo=node.js)](https://nodejs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

聊天 · 工具 Agent · 执行时间线 · 插件化工具 · 长期记忆 · 任务编排 · 设备画像 · 习惯体检 · TTS

</div>

---

BKLT 黑光（BLACKLIGHT，旧名/内部兼容名：ONYX-OVERRIDE）不是普通聊天机器人，而是一个本地优先的 AI Agent 自动化工作台。它通过 Electron + React + FastAPI 把模型、工具、记忆、任务执行和可视化过程整合在一起，让用户能看到 AI 在做什么、用了什么工具、结果是什么、哪里失败了、下一步准备做什么。

## 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    Electron 桌面壳                        │
│  ┌──────────────────────┐   ┌────────────────────────┐  │
│  │   React 前端 (3000)   │◄──►│  FastAPI 后端 (8000)   │  │
│  │  Agent 工作台 / 时间线 │   │  Agent · 工具 · 调度   │  │
│  └──────────────────────┘   └────────────┬───────────┘  │
└──────────────────────────────────────────┼──────────────┘
                                           │
                   ┌───────────────────────┼───────────────┐
                   │                       │               │
            ┌──────▼──────┐        ┌───────▼──────┐  ┌────▼─────┐
            │   Ollama    │        │  vLLM / NIM  │  │  F5-TTS  │
            │ 可选本地模型 │        │ OpenAI兼容接口│  │  语音合成  │
            └─────────────┘        └──────────────┘  └──────────┘
```

## 当前进化方向

| 方向 | 说明 |
|------|------|
| Agent 工作台 | 把每次任务拆成 thinking、tool_call、tool_result、final_answer 等可视化步骤 |
| 插件化工具 | 工具拥有分组、描述、风险等级、参数 schema，方便前端渲染工具面板 |
| 记忆树 | 长期记忆、playbook、技能包和本地知识库共同组成可压缩上下文 |
| 自动化执行 | 支持文件读写、代码执行、网页搜索、浏览器自动化、项目检查和任务编排 |
| 安全分层 | 工具按 safe / confirm / dangerous 分层，为后续确认弹窗和权限控制做准备 |

## 快速开始

### 环境要求

| 依赖 | 最低版本 |
|------|----------|
| Python | 3.10 |
| Node.js | 18 LTS |
| Ollama **或** vLLM/OpenAI-compatible 网关 | 最新 |

### 一键启动（推荐）

```bash
# 1. 克隆
git clone https://github.com/uumingtian-max/ai-agent-project.git
cd ai-agent-project

# 2. 首次安装
pip install -r requirements-agent-api.txt
cd frontend && npm install && cd ..

# 3. 配置
cp backend/.env.example backend/.env
# 按需编辑 backend/.env

# 4. 准备模型网关
# 当前 BKLT 黑光推荐：本机 vLLM / OpenAI-compatible 网关，地址 http://127.0.0.1:8001/v1
# 兼容 Ollama 路线：ollama pull qwen3:14b

# 5. 启动
python start.py          # 桌面应用
python start.py dev      # 开发模式
python start.py mobile   # 手机访问模式
```

> **Windows 快捷方式**：双击桌面 `BKLT 黑光` 快捷方式。当前旧链路 `Launch-ONYX-OVERRIDE.vbs` 作为兼容入口保留，迁移时不要直接删除。

### 启动模式

| 命令 | 说明 |
|------|------|
| `python start.py` | 默认：Electron 桌面应用 |
| `python start.py dev` | 开发模式（热重载） |
| `python start.py backend` | 仅后端 API |
| `python start.py mobile` | 局域网/Tailscale 手机访问 |
| `python start.py vllm` | 本机 vLLM 路线 |
| `python start.py tts` | 仅启动 F5-TTS |

## 功能说明

### 模式

| 模式 | 说明 |
|------|------|
| **聊天** | 问答与建议，不自动改文件 |
| **Agent** | 自动选工具、调用工具、压缩结果并输出执行过程 |

### 斜杠命令

| 命令 | 作用 |
|------|------|
| `/doctor` | 系统自检 |
| `/dashboard` | 总控台 |
| `/skills` | 技能库 |
| `/scheduler` | 定时任务 |
| `/mode chat` / `/mode agent` | 切换模式 |
| `/model nvidia/Gemma-4-26B-A4B-NVFP4` | 切换到当前推荐 Gemma 4 模型 |
| `/model qwen3:14b` | 切换到 Ollama 示例模型 |
| `/skill <id>` | 挂载指定技能 |
| `/tools` | 列出 Agent 工具 |

## 配置

复制并编辑 `backend/.env`：

```bash
cp backend/.env.example backend/.env
```

核心配置项：

```env
# 当前 BKLT 黑光推荐：OpenAI-compatible 本地模型网关
LLM_BACKEND=openai_compatible
OPENAI_BASE_URL=http://127.0.0.1:8001/v1
OPENAI_API_KEY=local
AGENT_DEFAULT_MODEL=nvidia/Gemma-4-26B-A4B-NVFP4

# 服务端口
BACKEND_PORT=8000

# 习惯体检
HABIT_CHECK_ENABLED=true
HABIT_CHECK_HOURS=9,21
```

完整配置见 [`backend/.env.example`](backend/.env.example)。

## API 参考

后端运行于 `http://localhost:8000`，交互式文档：`http://localhost:8000/docs`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 存活检测 |
| GET | `/meta/doctor` | 系统自检 |
| GET | `/meta/skills` | 技能目录 |
| GET | `/meta/models` | 模型列表 |
| GET | `/meta/tools/registry` | UI 可直接使用的结构化工具注册表 |
| GET | `/meta/tools/risks` | 工具风险分层摘要 |
| POST | `/chat/` | 聊天（SSE 流式） |
| POST | `/agent/run` | Agent 执行（SSE 流式） |
| GET | `/agent/tools` | 兼容旧版工具清单 |
| GET | `/scheduler/jobs` | 定时任务列表 |
| GET | `/meta/habit` | 习惯体检状态 |
| POST | `/meta/habit/run` | 立即执行体检 |
| GET | `/automation/capabilities` | 自动化能力清单 |
| GET | `/automation/jobs` | 自动化任务列表 |
| POST | `/automation/run` | 立即执行一次自动化任务 |
| GET | `/automation/runs` | 自动化运行记录 |
| GET | `/automation/events` | 自动化可视化事件流 |

## Agent 工具系统

结构化工具注册表位于 `backend/tool_registry.py`，用于支持：

- 工具面板展示
- 工具分组
- 参数 schema
- safe / confirm / dangerous 风险标记
- 后续执行前确认和插件市场

更多说明见 [`docs/TOOLS.md`](docs/TOOLS.md)。

## 技能包

86+ 条 Markdown 技能位于 `backend/agent_skills/`，带 `triggers:` 行自动挂载。

优化技能质量：
```bash
python scripts/optimize-agent-skills-deep.py
```

## 习惯体检

后端每天 **9:00 / 21:00** 自动执行：

1. `/meta/doctor` 本机体检
2. 行为采样分析（窗口 / 进程 / 工具成功率）
3. 写入 playbook 记忆
4. 行为变化时更新 `backend/agent_skills/learned_habit_auto.md`

报告保存在 `outputs/habit_checks/`。

## 文档

| 文档 | 说明 |
|------|------|
| [`docs/BKLT_BLACKLIGHT_MAINTENANCE.md`](docs/BKLT_BLACKLIGHT_MAINTENANCE.md) | BKLT 黑光维护基线、少确认规则、启动链路和排障顺序 |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 架构与执行链路 |
| [`docs/TOOLS.md`](docs/TOOLS.md) | 工具系统、风险等级、插件化规范 |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | 开发、测试、CI、发布流程 |
| [`docs/AGENT_WORKBENCH_EVOLUTION.md`](docs/AGENT_WORKBENCH_EVOLUTION.md) | Agent 工作台进化路线 |

## Docker 部署（服务器/无头模式）

```bash
# 构建并启动（Ollama + 后端 + 前端 nginx）
docker compose up -d

# 查看日志
docker compose logs -f backend

# 停止
docker compose down
```

## 故障排除

| 现象 | 排查 |
|------|------|
| 模型不说话 | 先检查 `http://127.0.0.1:8001/v1/models`；Ollama 路线再检查 11434 |
| Agent 无步骤 | 确认 Agent 模式；`/doctor` 查看模型后端状态 |
| 工具面板为空 | 检查 `/meta/tools/registry` 是否返回 `ok: true` |
| 自动化面板为空 | 检查 `/automation/capabilities`、`/automation/events` |
| 图标不对 | `python scripts/refresh_icon.py` |
| 端口冲突 | 修改 `backend/.env` 中 `BACKEND_PORT` |

## 目录结构

```
ai-agent-project/
├── backend/          FastAPI + Agent + 技能包
│   ├── agent_skills/ 86+ 条 Markdown 技能
│   ├── tools/        Agent 工具实现
│   ├── tool_registry.py 结构化工具元数据
│   ├── .env.example  完整配置模板
│   └── Dockerfile
├── frontend/         React UI
├── electron/         桌面 Electron 壳
├── docs/             架构、工具、开发与进化路线文档
├── scripts/          工具脚本（vLLM、图标、打包…）
├── assets/branding/  品牌图资源
├── start.py          ★ 统一启动器（保留旧脚本兼容）
└── docker-compose.yml
```

## 贡献

欢迎 PR！请先 `ruff check backend/` 通过再提交。

## License

MIT © uumingtian-max
