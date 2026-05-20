# BT（黑光）— 持久记忆 AI Agent 工作台

**一个随时间成长的本地 AI Agent。每次对话、每次执行，都在让它更懂你。**

[![CI](https://github.com/uumingtian-max/ai-agent-project/actions/workflows/ci.yml/badge.svg)](https://github.com/uumingtian-max/ai-agent-project/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Node](https://img.shields.io/badge/Node.js-18%2B-green?logo=node.js)](https://nodejs.org)
[![Ollama](https://img.shields.io/badge/Ollama-ready-black?logo=ollama)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)
[![CLAUDE.md](https://img.shields.io/badge/CLAUDE.md-agent%20ready-blueviolet)](./CLAUDE.md)
[![Skills](https://img.shields.io/badge/skills-3%20exported-orange)](./skills/)

聊天 · 工具 Agent · 执行时间线 · 智能模型路由 · 持久记忆 · 习惯体检 · 技能自进化 · TTS

---

> BT（黑光）不是无状态聊天窗口。它记住你的习惯、学习你的工作方式、在每次执行后自动更新技能包。
> 你的数据完全在本机，模型完全自选，没有云端依赖。

旧名 / 兼容名：BKLT 黑光、ONYX-OVERRIDE

目录说明见 **[docs/PROJECT_LAYOUT.md](docs/PROJECT_LAYOUT.md)**。Windows 一键启动见 **[`launcher/README.md`](launcher/README.md)**。AI 编程 Agent（Claude Code / Cursor）使用规范见 **[`CLAUDE.md`](./CLAUDE.md)**。

## 为什么选 BT（黑光）

| | BT（黑光）| 普通聊天 AI | 云端 Agent |
|---|---|---|---|
| 数据位置 | 完全本机 | 云端 | 云端 |
| 跨会话记忆 | ✅ 持久 SQLite + 向量索引 | ❌ 无 | ✅ 但在服务商 |
| 模型自选 | ✅ Ollama / vLLM / llama.cpp | ❌ 锁定 | ❌ 锁定 |
| 技能自进化 | ✅ 习惯体检 + 自动更新技能包 | ❌ 无 | 部分 |
| 可视化执行 | ✅ 每步 thinking/tool/result | ❌ 无 | 部分 |
| 成本 | 一次性硬件 | 按量 | 按量 |

## 架构总览

```text
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
            ┌──────▼──────┐        ┌───────▼──────┐  ┌──────▼─────┐  │
            │   Ollama    │        │ llama.cpp /  │  │  F5-TTS   │  │
            │ 多模型栈     │        │ vLLM :8001   │  │  语音合成  │  │
            └─────────────┘        └──────────────┘  └────────────┘  │
```

### 智能模型路由（5090 · 五模型栈示例）

| 模型 | 大小 | 职责 |
|------|------|------|
| nomic-embed-text | 0.3G | 向量嵌入 · RAG · 记忆召回 |
| functiongemma | 0.3G | 工具路由 · 意图解析 |
| qwen3.5:9b | 8.6G | 主脑 · 快答 · 编排审查 |
| deepseek-r1:7b | 4.7G | 推理 · 规划 · 自我进化 |
| deepseek-coder-v2:16b | 8.9G | 复杂代码（按需加载）|

详见 [`skills/smart-model-routing.md`](./skills/smart-model-routing.md)

## 核心能力

| 能力 | 说明 |
| ------ | ------ |
| **持久记忆** | SQLite + 向量索引，跨会话记住你的习惯和偏好，详见 [`skills/persistent-memory.md`](./skills/persistent-memory.md) |
| **Agent 工作台** | 每次任务拆成 thinking → tool_call → tool_result → final_answer，全程可视化 |
| **智能模型路由** | 按任务类型选最小合适模型，详见 [`skills/smart-model-routing.md`](./skills/smart-model-routing.md) |
| **习惯体检** | 每天 9:00 / 21:00 自动执行，行为变化时更新技能包，详见 [`skills/habit-check.md`](./skills/habit-check.md) |
| **插件化工具** | 工具有分组、描述、风险等级、参数 schema，方便前端渲染 |
| **技能自进化** | Agent 执行后异步记录进化日志，定期压缩写回技能包 |
| **安全分层** | 工具按 safe / confirm / dangerous 分层，dangerous 操作须 confirmed=true |

## 快速开始

### 环境要求

| 依赖 | 最低版本 |
| ------ | ---------- |
| Python | 3.10 |
| Node.js | 18 LTS |
| llama.cpp **或** Ollama（OpenAI 兼容网关） | 见 `docs/setup/LLAMA_CPP.md` |

### 一键启动（推荐）

#### Windows（本机常用）

1. 首次：双击 `launcher\INSTALL_FIRST_RUN.bat`（装 Node / Python 依赖并构建前端）
2. 配置：`copy backend\.env.local-llamacpp.example backend\.env`（按你的 GGUF 路径改 `LLAMA_CPP_*`）
3. 启动：双击 `launcher\START_APP.bat`（会自动拉起 llama.cpp，再开桌面）
4. 仅模型网关：`launcher\打开本机Gemma模型.cmd`

根目录 `START_APP.bat` 会转调到 `launcher\`（兼容旧快捷方式）。桌面快捷方式请指向 `launcher\Launch-BT-Heiguang.vbs`（无黑框）。

改完 `frontend/index.html` 或前端源码后，桌面模式需重新构建：

```bat
npm run build --prefix frontend
```

#### 命令行（跨平台）

```bash
git clone https://github.com/uumingtian-max/ai-agent-project.git
cd ai-agent-project

pip install -r requirements.txt
npm install && npm install --prefix frontend

cp backend/.env.local-llamacpp.example backend/.env   # Windows: copy ...
# 编辑 backend/.env 中的 LLAMA_CPP_MODEL / LLAMA_CPP_MMPROJ

python start.py          # 桌面应用
python start.py dev      # 开发模式
python start.py mobile   # 手机访问模式
```

模型与 llama.cpp 细节见 [`docs/setup/LLAMA_CPP.md`](docs/setup/LLAMA_CPP.md)。

### 启动模式

| 命令 | 说明 |
| ------ | ------ |
| `python start.py` | 默认：Electron 桌面应用 |
| `python start.py dev` | 开发模式（热重载） |
| `python start.py backend` | 仅后端 API |
| `python start.py mobile` | 局域网/Tailscale 手机访问 |
| `launcher\START_VLLM_GEMMA4.bat` + `launcher\START_APP_LOCAL.bat` | 实验性 vLLM 路线（非默认） |
| `python start.py tts` | 仅启动 F5-TTS |

## 功能说明

### 模式

| 模式      | 说明                                           |
| --------- | ---------------------------------------------- |
| **聊天**  | 问答与建议，不自动改文件                       |
| **Agent** | 自动选工具、调用工具、压缩结果并输出执行过程   |

### 斜杠命令

| 命令 | 作用 |
| ------ | ------ |
| `/doctor` | 系统自检 |
| `/dashboard` | 总控台 |
| `/skills` | 技能库 |
| `/scheduler` | 定时任务 |
| `/mode chat` / `/mode agent` | 切换模式 |
| `/model Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced-Q5_K_P` | 切换到当前锁定的 llama.cpp 模型（须与 `.env` 一致） |
| `/model qwen3.5:9b` | 切换到 Ollama 主脑模型（须与 `.env` 一致） |
| `/skill <id>` | 挂载指定技能 |
| `/tools` | 列出 Agent 工具 |

## 配置

本机多模态 llama.cpp（当前默认）：

```bat
copy backend\.env.local-llamacpp.example backend\.env
```

核心项（须与 `http://127.0.0.1:8001/v1/models` 返回的 `id` 一致）：

```env
LLM_BACKEND=openai_compatible
OPENAI_BASE_URL=http://127.0.0.1:8001/v1
AGENT_DEFAULT_MODEL=Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced-Q5_K_P
LLAMA_CPP_EXE=C:\llama-cpp\llama-server.exe
LLAMA_CPP_MODEL=...\Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced-Q5_K_P.gguf
LLAMA_CPP_MMPROJ=...\mmproj-Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced-f16.gguf
BACKEND_PORT=8000
```

根目录 [`.env.example`](.env.example) 仅作说明；实际配置写在 `backend/.env`。Ollama 路线用 [`backend/.env.example`](backend/.env.example)。改 `.env` 后需重启应用。

## API 参考

后端运行于 `http://localhost:8000`，交互式文档：`http://localhost:8000/docs`

| 方法 | 路径 | 说明 |
| ------ | ------ | ------ |
| GET | `/health` | 存活检测 |
| GET | `/meta/doctor` | 系统自检 |
| GET | `/meta/skills` | 技能目录 |
| GET | `/meta/models` | 模型列表 |
| GET | `/meta/tools/registry` | **稳定接口**：UI 工具面板 / 启动探针（`ok` + `tools` + `groups`） |
| GET | `/meta/tools/full` | 兼容别名：完整注册表 + 风险统计（新集成优先用 registry） |
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
| ------ | ------ |
| [`docs/PROJECT_LAYOUT.md`](docs/PROJECT_LAYOUT.md) | 项目目录分工、推荐入口和根目录保留原则 |
| [`docs/setup/LLAMA_CPP.md`](docs/setup/LLAMA_CPP.md) | 本机 llama.cpp 多模态 Gemma 配置与排障 |
| [`docs/BKLT_BLACKLIGHT_MAINTENANCE.md`](docs/BKLT_BLACKLIGHT_MAINTENANCE.md) | 维护基线、启动链路与排障 |
| [`launcher/README.md`](launcher/README.md) | 一键启动脚本说明 |
| [`docs/DESKTOP_CONSOLIDATION.md`](docs/DESKTOP_CONSOLIDATION.md) | 桌面目录合并说明 |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 架构与执行链路 |
| [`docs/TOOLS.md`](docs/TOOLS.md) | 工具系统、风险等级、插件化规范 |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | 开发、测试、CI、发布流程 |
| [`docs/AGENT_WORKBENCH_EVOLUTION.md`](docs/AGENT_WORKBENCH_EVOLUTION.md) | Agent 工作台进化路线 |
| [`docs/setup/F5_TTS_SETUP.md`](docs/setup/F5_TTS_SETUP.md) | F5-TTS 安装与隔离环境说明 |
| [`docs/setup/REAL_VOICE_TTS.md`](docs/setup/REAL_VOICE_TTS.md) | 语音相关补充说明 |
| [`docs/mobile/IPHONE_INSTALL.md`](docs/mobile/IPHONE_INSTALL.md) | iPhone 安装与接入说明 |
| [`docs/mobile/REMOTE_MOBILE_ACCESS.md`](docs/mobile/REMOTE_MOBILE_ACCESS.md) | 局域网 / 远程手机访问说明 |
| [`docs/training/GEMMA_EVOLUTION_TRAINING.md`](docs/training/GEMMA_EVOLUTION_TRAINING.md) | Gemma 训练路线记录 |

## Docker 部署（服务器/无头模式）

```bash
# 构建并启动（Ollama + 后端 + 前端 nginx）
docker compose -f docs/deploy/docker-compose.yml up -d

docker compose -f docs/deploy/docker-compose.yml logs -f backend
docker compose -f docs/deploy/docker-compose.yml down
```

## 故障排除

| 现象 | 排查 |
| ------ | ------ |
| 模型不说话 | 先检查 `http://127.0.0.1:8001/v1/models`；Ollama 路线再检查 11434 |
| Agent 无步骤 | 确认 Agent 模式；`/doctor` 查看模型后端状态 |
| 工具面板为空 | 检查 `/meta/tools/registry` 是否返回 `ok: true` |
| 自动化面板为空 | 检查 `/automation/capabilities`、`/automation/events` |
| 启动屏无图标 | 确认 `electron/icon-128.png` 存在；运行 `npm run branding` 或 `python scripts/build-branding.py` |
| 桌面标题/图标仍像旧版 | 执行 `npm run build --prefix frontend`（Electron 读 `frontend/build/index.html`，不是源 `index.html`） |
| 图标/Logo 不对 | `npm run branding`，会同步 `frontend/public` 与 `electron/` |
| 端口冲突 | 修改 `backend/.env` 中 `BACKEND_PORT`；前端构建时 `REACT_APP_API_URL` 须与后端一致 |

## 目录结构

```text
ai-agent-project/
├── backend/          FastAPI + Agent + 技能包
├── frontend/         React UI
├── electron/         桌面壳（splash.html、启动图标）
├── launcher/         一键启动（START_APP.bat 等）
├── docs/             文档（含 deploy/docker-compose.yml）
├── scripts/          工具脚本
├── assets/           品牌资源
├── data/             本机数据（知识库等）
├── archive/          历史快照（勿作日常目录）
├── skills/           可复用技能文档（对外展示 / fork）
├── CLAUDE.md         Claude Code / Cursor Agent 说明
├── start.py          统一启动入口
├── README.md
├── .env.example
└── requirements.txt
```

完整说明见 [`docs/PROJECT_LAYOUT.md`](docs/PROJECT_LAYOUT.md)。

## 贡献

欢迎 PR！请先 `ruff check backend/` 通过再提交。

## License

MIT © [uumingtian-max](https://github.com/uumingtian-max)
