# BT（黑光）— ai-agent-project 文件清单与说明

> **生成日期：** 2026-05-20  
> **GitHub：** https://github.com/uumingtian-max/ai-agent-project  
> **本地路径：** `C:\Users\ROG\Desktop\ai-agent-project`  
> **用途：** 单独整理项目里有哪些文件、各自干什么、日常要不要碰。

---

## 零、GitHub 仓库（线上版）

| 项目 | 说明 |
|------|------|
| **仓库地址** | https://github.com/uumingtian-max/ai-agent-project |
| **可见性** | Public（公开） |
| **默认分支** | `main`（约 122 次提交） |
| **开发分支** | `feature/bklt-stable-automation` |
| **本地 remote** | `origin` → 已指向上述仓库 |

### 克隆（新机器用）

```bash
git clone https://github.com/uumingtian-max/ai-agent-project.git
cd ai-agent-project
pip install -r requirements.txt
npm install && npm install --prefix frontend
copy backend\.env.local-llamacpp.example backend\.env
python start.py
```

### 本地 vs 线上（当前状态）

- 你本机在分支 **`feature/bklt-stable-automation`**，与远程该分支**已同步**（最新 commit：`d513f65`）
- 有少量**未提交**本地改动：`Launch-BKLT-Blacklight.vbs`、`electron/icon-128.png`、`scripts/package-desktop-zip.ps1` 等
- **`data/knowledge-vault/`**、**`backend/*.db`** 等本机数据**不进 Git**（只在本地）

### GitHub 上有的顶层目录

`.cursor` · `.github` · `.vscode` · `archive` · `assets` · `backend` · `data` · `docs` · `electron` · `frontend` · `launcher` · `scripts` · `skills` · `vendor`  
以及根目录：`start.py`、`README.md`、`CLAUDE.md`、`requirements.txt`、`package.json` 等

---

## 一、项目是做什么的

**BT（黑光）** = 本地优先、带持久记忆的 AI Agent 工作台。

- 后端：Python + FastAPI（Agent、工具、记忆、调度）
- 前端：React + Vite
- 桌面：Electron 壳
- 模型：Ollama / llama.cpp / vLLM（通过 `model_router.py` 路由）

---

## 二、顶层目录一览（先看这个）

| 目录/文件 | 备注 | 日常要不要碰 |
|-----------|------|--------------|
| `backend/` | 核心：API、Agent、工具、记忆、96 个 agent 技能 | **常改** |
| `frontend/` | React 聊天/工作台 UI | 改界面时 |
| `electron/` | 桌面窗口、splash、图标 | 改桌面壳时 |
| `launcher/` | 双击启动的 bat/vbs/cmd | 启动用 |
| `docs/` | 架构、部署、LLM、维护文档 | 查说明时 |
| `scripts/` | 安装、诊断、测试、模型脚本 | 装环境/排障 |
| `skills/` | 根目录 3 个通用技能（.md） | 偶尔 |
| `assets/` | 品牌图标、Logo | 换品牌时 |
| `data/` | **本机数据**（知识库、DB，不进 Git） | 运行时自动写 |
| `vendor/` | 外仓对照（agency-agents 等） | 对照更新技能时 |
| `archive/` | 历史快照 | **不要**当工作目录 |
| `.cursor/` | Cursor IDE 规则与技能 | 在 Cursor 开发时 |
| `.github/` | CI / Release 工作流 | 发版/CI 时 |
| `files-extracted/` | 从别处解压的参考片段 | 参考用 |
| `logs/`、`outputs/`、`tmp/` | 运行日志与临时输出 | 自动产生 |
| `node_modules/` | Node 依赖（npm install） | 不要手改 |

---

## 三、根目录文件（项目入口）

| 文件 | 备注 |
|------|------|
| `start.py` | **统一启动入口**（`python start.py` / `python start.py dev`） |
| `START_APP.bat` | 转发到 `launcher/START_APP.bat`（兼容旧快捷方式） |
| `Launch-BT-Heiguang.vbs` | 桌面启动脚本（根目录副本） |
| `Launch-BKLT-Blacklight.vbs` | 黑光启动脚本 |
| `Launch-ONYX-OVERRIDE.legacy.vbs` | 旧 ONYX 覆盖启动（遗留） |
| `README.md` | 项目说明 |
| `CLAUDE.md` | 给 AI 编程助手看的编码规范 |
| `package.json` / `package-lock.json` | Electron / Node 元数据 |
| `requirements.txt` | Python 依赖入口（常指向 backend） |
| `requirements-agent-api.txt` | Agent API 额外依赖 |
| `pyproject.toml` | Python 项目配置（ruff 等） |
| `pyrightconfig.json` | 类型检查配置 |
| `.env` / `.env.example` | 环境变量（**真配置多在 `backend/.env`**） |
| `ai-agent-project.code-workspace` | VS Code / Cursor 工作区 |
| `.gitignore` / `.gitattributes` | Git 规则 |
| `.python-version` | Python 版本锁定 |
| `.hintrc` | 前端 HTML 提示配置 |

---

## 四、backend/ — 后端核心（最重要）

### 4.1 主流程与 Agent

| 文件 | 备注 |
|------|------|
| `main.py` | FastAPI 应用入口、路由挂载 |
| `agent.py` | Agent 主循环 |
| `agent_runtime.py` | 运行时状态 |
| `agent_session.py` | 会话管理 |
| `agent_prompts.py` | 系统提示词 |
| `agent_policy.py` | Agent 策略 |
| `agent_dispatch.py` | 任务分发 |
| `agent_events.py` / `agent_run_events.py` | 事件流（SSE 用） |
| `agent_progress.py` | 进度上报 |
| `agent_tool_map.py` | 工具映射 |
| `agent_task_brief.py` | 任务摘要 |
| `chat.py` | 聊天接口 |
| `subagent_runner.py` | 子 Agent 并行执行 |

### 4.2 模型与 LLM

| 文件 | 备注 |
|------|------|
| `model_router.py` | **任务→模型路由**（改模型分配从这里） |
| `llm_client.py` | Ollama / OpenAI 兼容调用 |
| `ollama_pins.py` | Ollama 模型 pin |
| `model_lock.py` | 模型占用锁 |
| `orchestrator.py` | 编排器 |
| `orchestrator_model_pool.py` | 编排用模型池 |
| `intent_router.py` | 意图路由 |
| `adaptive_dispatch.py` | 自适应分发 |

### 4.3 记忆与知识

| 文件 | 备注 |
|------|------|
| `memory_store.py` | **持久记忆读写**（SQLite API） |
| `vector_memory.py` | 向量记忆 |
| `context_pack.py` | 上下文打包 |
| `habit_pipeline.py` | 习惯体检流水线 |
| `self_evolve.py` | 自进化相关 |

### 4.4 工具与能力

| 文件 | 备注 |
|------|------|
| `tool_registry.py` | **工具注册表**（新增工具要登记） |
| `tool_registry_routes.py` | 工具注册 API |
| `capability_registry.py` | 能力注册 |
| `capability_executor.py` | 能力执行 |
| `capability_runtime.py` | 能力运行时 |
| `capability_routes.py` | 能力 API |
| `capability_prompt_rules.py` | 能力提示规则 |
| `specialist_registry.py` | 专家 Agent 注册 |

### 4.5 技能与 SkillHub

| 文件 | 备注 |
|------|------|
| `skill_pack.py` | 技能包加载 |
| `skillhub.py` / `skillhub_routes.py` | SkillHub 服务 |
| `agent_skills/*.md` | **96 个 Agent 技能**（见下文完整列表） |

### 4.6 路由与功能模块

| 文件 | 备注 |
|------|------|
| `scheduler_routes.py` / `scheduler_store.py` / `scheduler_runner.py` | 定时任务 |
| `automation_routes.py` / `automation_store.py` / `automation_runner.py` | 自动化 |
| `gateway_routes.py` | 网关 |
| `mcp_routes.py` | MCP 协议 |
| `meta_routes.py` | 元信息 |
| `notebook_routes.py` | 笔记本 |
| `telegraf_routes.py` | Telegraf 信号 |
| `content_routes.py` / `content_pipeline.py` | 内容流水线 |
| `local_agent_api.py` | 本地 Agent API |
| `f5_tts_server.py` | F5-TTS 语音 |
| `video_gen.py` | 视频生成 |
| `a2a_bridge.py` | Agent-to-Agent 桥接 |

### 4.7 基础设施

| 文件 | 备注 |
|------|------|
| `settings.py` | Pydantic 配置（读 `.env`） |
| `env_bootstrap.py` | 环境初始化 |
| `safe_paths.py` | **安全路径**（文件操作必须走这里） |
| `paths.py` | 路径常量 |
| `policy_guard.py` | 策略守卫 |
| `observe.py` | 观察/遥测 |
| `visual_event_bus.py` | 可视化事件总线 |
| `request_log.py` | 请求日志 |
| `sqlite_wal.py` | SQLite WAL |
| `media_fallback.py` | 媒体回退 |
| `hooks.py` | 钩子 |

### 4.8 backend/tools/ — 具体工具实现

| 文件 | 备注 |
|------|------|
| `browser.py` | 浏览器 / Playwright |
| `code_exec.py` | 执行 Python |
| `db_query.py` | 数据库查询 |
| `external_control.py` | 外部控制（桌面等） |
| `file_ops.py` | 文件读写 |
| `http_tool.py` | HTTP 请求 |
| `local_crawl.py` | 本地爬取 |
| `mcp_invoke.py` | 调用 MCP |
| `search.py` | 搜索 |

### 4.9 backend/tests/ — 测试（改后端应跑）

`pytest backend/tests/ -q`

共 22 个测试模块，例如：`test_agent_run_loop.py`、`test_tool_registry.py`、`test_capability_executor.py` 等。

### 4.10 backend 配置与运行时 DB

| 路径 | 备注 |
|------|------|
| `backend/.env` | **真实配置**（密钥、模型名，不进 Git） |
| `backend/.env.example` | 配置模板 |
| `backend/behavior.db` | 行为库（运行时） |
| `backend/memory.db` | 记忆库（运行时） |

---

## 五、backend/agent_skills/ — 96 个技能文件

每个 `.md` 是一份 Agent 可加载的任务 playbook。

```
a2a_interop_lite.md
academic_research_pipeline.md
agency_api_tester.md
agency_backend_architect.md
agency_code_reviewer.md
agency_dev_orchestrator.md
agency_mcp_builder.md
agency_reality_checker.md
agency_security_engineer.md
agent_forced_skill.md
agent_plan_diff_review.md
anything_to_notebook_workflow.md
api_contract_design.md
bt_external_repos.md
chat_streaming_ux.md
claude_skills_domain_map.md
codebase_context_first.md
codex_lb_routing.md
creative_delivery_pipeline.md
design_stitch_handoff.md
docs_readme_changelog.md
fastapi_route_debug.md
feature_chat_memory.md
feature_evolution.md
feature_gateway.md
feature_habit_pipeline.md
feature_observe.md
feature_orchestrator.md
feature_scheduler.md
feature_telegraf.md
feature_workflow.md
gaussian_splatting_creative.md
git_worktree_workflow.md
git_wt_parallel.md
github_trending_developers.md
gstack_agent_roles.md
knowledge_vault_ingest.md
learned_habit_auto.md
llm_coding_pitfalls.md
local_deep_research.md
local_transcription.md
mecha_policy_workflow.md
memory_eval_consolidation.md
model_pin_roles.md
monthly_trend_map.md
multi_provider_llm_routing.md
multimodal_desktop_agent.md
network_tunnel_legitimate.md
npm_supply_chain_safety.md
onyx_electron_desktop.md
onyx_frontend_react.md
onyx_ollama_ops.md
onyx_packaging_release.md
orchestration_handoff.md
persistent_context.md
personal_local_super_agent.md
plannotator_style_gate.md
recursive_long_document.md
rlm_recursive_reasoning.md
ruflo_style_swarm.md
scientific_hypothesis_tables.md
security_local_audit.md
situational_intel_observe.md
skills_master_index.md
slash_commands_operator.md
social_source_to_skill.md
spec_minimal_steps.md
sqlite_ops_playbook.md
stitch_mcp_ui.md
swarm_orchestration_lite.md
telegraf_memory_signals.md
token_efficiency_signals.md
tool_browser_playwright.md
tool_desktop_context.md
tool_execute_python.md
tool_filesystem.md
tool_http_request.md
tool_local_search.md
tool_mcp_invoke.md
tool_media_gen.md
tool_notebook.md
tool_open_navigate.md
tool_parallel_subagents.md
tool_project_check.md
tool_query_database.md
tool_reliability.md
tool_skill_authoring.md
tool_task_orchestration.md
tool_web_search.md
tool_windows_gui.md
trading_automation_boundaries.md
transcribe_whisper_local.md
trend_playbook_snapshot.md
vibe_coding_pedagogy.md
weekly_trend_map.md
worldmonitor_observe.md
```

---

## 六、frontend/ — 前端 UI

| 路径 | 备注 |
|------|------|
| `src/App.js` | 主应用 |
| `src/index.js` | 入口 |
| `src/App.css` / `CleanHome.css` | 样式 |
| `src/AutomationDashboard.js` | 自动化面板 |
| `src/OperatorPanels.js` | 操作面板 |
| `src/NeuralTopology.jsx` | 神经网络拓扑可视化 |
| `src/workbenchApi.js` | 工作台 API |
| `src/automationApi.js` | 自动化 API |
| `src/modelCatalog.js` | 模型目录 |
| `src/clipboardAttachments.js` | 剪贴板附件 |
| `src/BrandLogo.js` | 品牌 Logo 组件 |
| `public/manifest.json` | PWA manifest |
| `public/*.png` / `favicon.ico` | 图标资源 |
| `vite.config.js` | Vite 构建配置 |
| `package.json` | 前端依赖 |
| `frontend/build/` | 构建产物（**不进 Git**） |

---

## 七、electron/ — 桌面壳

| 文件 | 备注 |
|------|------|
| `main.js` | Electron 主进程 |
| `preload.js` | 预加载脚本 |
| `splash.html` | 启动闪屏 |
| `icon.ico` / `icon.png` 等 | 应用图标 |

---

## 八、launcher/ — 一键启动

| 文件 | 备注 |
|------|------|
| `START_APP.bat` | **主启动**（推荐） |
| `START_DEV.bat` | 开发模式 |
| `START.bat` / `START_APP_LOCAL.bat` | 其他启动变体 |
| `START_MOBILE.bat` | 手机远程访问 |
| `START_VLLM_GEMMA4.bat` | 启动 vLLM Gemma |
| `Launch-BT-Heiguang.vbs` | VBS 静默启动 |
| `INSTALL_FIRST_RUN.bat` | 首次安装 |
| `INSTALL_OLLAMA_2026.bat` | 安装 Ollama 栈 |
| `INSTALL_F5_TTS.bat` | 安装 F5-TTS |
| `MANAGE_MODELS.bat` | 模型管理 |
| `打开AI Agent.cmd` / `打开本机Gemma模型.cmd` | 中文快捷入口 |
| `README.md` | 启动器说明 |

---

## 九、docs/ — 文档

| 文件 | 备注 |
|------|------|
| `PROJECT_LAYOUT.md` | **目录结构说明**（与本文互补） |
| `ARCHITECTURE.md` | 架构 |
| `DEVELOPMENT.md` | 开发指南 |
| `TOOLS.md` | 工具说明 |
| `BKLT_BLACKLIGHT_MAINTENANCE.md` | 维护基线 |
| `BKLT_SKILLHUB_DESIGN.md` | SkillHub 设计 |
| `AGENT_WORKBENCH_EVOLUTION.md` | 工作台演进 |
| `OLLAMA_STACK_5090.md` / `OLLAMA_STACK_2026_FLAGSHIP.md` | Ollama 模型栈 |
| `setup/LLAMA_CPP.md` | llama.cpp 配置 |
| `setup/F5_TTS_SETUP.md` / `REAL_VOICE_TTS.md` | 语音 TTS |
| `mobile/IPHONE_INSTALL.md` / `REMOTE_MOBILE_ACCESS.md` | 手机访问 |
| `deploy/docker-compose.yml` | Docker 部署 |
| `training/GEMMA_EVOLUTION_TRAINING.md` | Gemma 训练 |

---

## 十、scripts/ — 工具脚本（节选分类）

### 环境与安装
`ensure-ollama.ps1`、`ensure-llama-cpp.ps1`、`ensure-runtime.ps1`、`install-onyx.ps1`、`setup-complete.ps1`

### 模型与 GPU
`MANAGE_MODELS.ps1`、`pin-ollama-models.ps1`、`install-gemma-weights.ps1`、`setup-local-gemma4-vllm.ps1`、`verify-vllm-python-wsl.sh`

### 测试与诊断
`run-agent-smoke.ps1`、`hammer-test.ps1`、`verify-tools.ps1`、`test-all-tools-live.py`、`restart-backend.ps1`

### 技能与记忆
`expand-agent-skills.py`、`build-skill-embedding-index.py`、`clean-memory-db.py`、`seed-identity-memory.py`

### 打包与桌面
`package-desktop-zip.ps1`、`create-desktop-shortcut.ps1`、`zip-project-to-desktop.ps1`

### 外仓同步
`sync-bt-vendor-repos.ps1`

> 完整列表约 60+ 个脚本，均在 `scripts/` 目录；`__pycache__/` 为 Python 缓存，可忽略。

---

## 十一、其他目录

### skills/（根目录，3 个）
- `habit-check.md` — 每日习惯体检
- `persistent-memory.md` — 持久记忆
- `smart-model-routing.md` — 智能模型路由

### assets/branding/
品牌图标全套（16px～1024px、ico、hero 图等）

### data/（本机，不进 Git）
| 路径 | 备注 |
|------|------|
| `data/knowledge-vault/` | 知识库 Markdown（当前约 **473** 个 `memory_*.md` + 分类索引） |
| `data/imported-assets/` | 导入的外部资产 |

### vendor/
- `repos.manifest.json` — 外仓清单
- `agency-agents/` — 对照用 Agent 角色库（克隆体，很大）

### .cursor/
| 路径 | 备注 |
|------|------|
| `rules/*.mdc` | Cursor 编码规则（agency、安全、质量等） |
| `skills/skill-creator-quality/SKILL.md` | 项目内技能编写指南 |

### .github/workflows/
- `ci.yml` — 持续集成
- `release.yml` — 发布

### archive/
历史 ONYX / 旧包快照 — **勿在此开发**

### files-extracted/
从 zip 解出的参考文件（如 `model_router.py`、`habit-check.md` 片段）

---

## 十二、不进 Git 的常见路径（了解即可）

```
node_modules/
frontend/build/
logs/
outputs/
tmp/
data/*.db
backend/.env
backend/behavior.db
backend/memory.db
vendor/agency-agents/   （完整克隆）
.pytest_cache/
.ruff_cache/
.venv-f5/
```

---

## 十三、怎么启动（速查）

| 方式 | 命令/文件 |
|------|-----------|
| Windows 双击 | `launcher/START_APP.bat` 或 `launcher/Launch-BT-Heiguang.vbs` |
| 命令行 | `python start.py`（桌面） / `python start.py dev`（开发） |
| 根目录兼容 | `START_APP.bat` → 转发到 launcher |

---

## 十四、日常开发改哪里（一句话）

| 想做什么 | 去哪个目录/文件 |
|----------|-----------------|
| 改 Agent 逻辑 | `backend/agent.py`、`agent_runtime.py` |
| 换模型分配 | `backend/model_router.py` + `backend/.env` |
| 加新工具 | `backend/tools/` + `backend/tool_registry.py` + 测试 |
| 加 Agent 技能 | `backend/agent_skills/xxx.md` |
| 改聊天 UI | `frontend/src/App.js` 等 |
| 改配置 | `backend/.env`（参考 `.env.example`） |
| 跑测试 | `pytest backend/tests/ -q` |

---

## 十五、项目路径快捷方式

- **源码根目录：** `C:\Users\ROG\Desktop\ai-agent-project`
- **本说明文件：** `C:\Users\ROG\Desktop\BT黑光-ai-agent-project-文件清单与说明.md`

---

*由 Cursor Agent 根据仓库实际扫描生成。若你新增文件，可让 Agent 重新生成或对照 `docs/PROJECT_LAYOUT.md` 更新。*
