# ONYX-OVERRIDE

本地 AI 助手桌面应用：聊天 + 工具 Agent + 技能包 + 设备画像。

## 快速启动

1. 安装 [Node.js](https://nodejs.org)、[Ollama](https://ollama.com)、Python 3.10+
2. **ZIP 便携包首次解压后**：运行 `INSTALL_FIRST_RUN.bat`
3. 二选一：
   - Ollama 路线：`ollama pull qwen3:14b`（或与 `backend/.env` 中 `AGENT_DEFAULT_MODEL` 一致）
   - 本机 vLLM 路线：准备 `nvidia/Gemma-4-26B-A4B-NVFP4` 到 `D:\models\Gemma-4-26B-A4B-NVFP4`
4. 双击桌面 **ONYX-OVERRIDE** 或运行 `START_APP.bat`
5. 本机 vLLM 模式：先运行 `scripts\START_VLLM_GEMMA4.bat`，再运行 `START_APP_LOCAL.bat`

### 打包到桌面 ZIP

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package-desktop-zip.ps1
```

生成 `桌面\ONYX-OVERRIDE-v1.1.0.zip`（不含 node_modules，约数十 MB）。

## 模式说明

| 模式 | 说明 |
|------|------|
| **聊天** | 问答与建议，不自动改文件 |
| **Agent** | 自动选工具：搜索、读写文件、浏览器、编排等 |

## 斜杠命令（输入框）

| 命令 | 作用 |
|------|------|
| `/doctor` | 打开系统自检 |
| `/dashboard` | 打开总控台 |
| `/skills` | 打开技能库 |
| `/scheduler` | 定时任务 |
| `/mode chat` / `/mode agent` | 切换模式 |
| `/model qwen3:14b` | 切换模型 |
| `/skill 技能id` | 下一条消息挂载指定技能 |
| `/tools` | 列出 Agent 工具 |

## 配置

复制 `backend/.env.example` → `backend/.env`，重点：

- `OLLAMA_HOST` — 默认 `http://127.0.0.1:11434`
- `AGENT_DEFAULT_MODEL` — 须与 `ollama list` 一致
- `LLM_BACKEND=openai_compatible` — 使用 NIM / vLLM / 9router 时配合 `OPENAI_BASE_URL`

## API（本机 8000）

- `GET /health` — 存活
- `GET /meta/doctor` — 系统自检
- `GET /meta/skills` — 技能目录
- `GET /meta/models` — 模型列表
- `POST /chat/` — 聊天（SSE）
- `POST /agent/run` — Agent（SSE）
- `GET /scheduler/jobs` — 定时任务
- `GET /meta/habit` — 习惯体检状态（每天两次）
- `POST /meta/habit/run` — 立即执行习惯体检

## 习惯体检与自我扩展

后端启动后 **每天 9:00 / 21:00（本地）** 自动执行：

1. `/meta/doctor` 本机体检  
2. 行为采样分析（窗口/进程/工具成功率）  
3. 写入 playbook 记忆  
4. 行为变化时更新 `backend/agent_skills/learned_habit_auto.md`  

配置见 `backend/.env.example`：`HABIT_CHECK_ENABLED`、`HABIT_CHECK_HOURS`、`HABIT_AUTO_SKILL`。  
报告保存在 `outputs/habit_checks/`。UI：**系统** 面板可查看状态并「立即习惯体检」。

## 技能包

Markdown 技能在 `backend/agent_skills/`（**86** 条，以 `GET /meta/skills` 的 `count` 为准），带 `triggers:` 行自动挂载。提质：`python scripts/optimize-agent-skills-deep.py`（Skill Creator 结构）。  
对标社区 [claude-skills](https://github.com/alirezarezvani/claude-skills) 与 [GitHub Trending Developers](https://github.com/trending/developers) 的**主题映射**模式，本仓库不克隆外仓。总索引：`skills_master_index`；热榜映射：`github_trending_developers`。

## 故障排除

- **模型不说话**：看顶部黄条 → Ollama 路线检查 11434；vLLM 路线检查 8001 → 点「重新检测」
- **Agent 无步骤**：确认在 Agent 模式，且后端 `/meta/doctor` 中 `ollama_reachable` 为 ok
- **图标不对**：运行 `scripts\refresh-desktop-icon.ps1`

## 目录

```
backend/          FastAPI + Agent + 技能包
frontend/         React UI
electron/         桌面壳
scripts/          启动、品牌图标、Ollama 检测
assets/branding/  品牌图生成产物
```
