# AGENTS.md — BT（黑光）Agent 协作说明

本文件给 Codex、GitHub Copilot、Claude Code、Cursor、Gemini/ADK 类 Agent 读取。更完整的维护说明见 `CLAUDE.md` 与 `docs/BKLT_BLACKLIGHT_MAINTENANCE.md`。

## 项目身份

- 对外名称：BT（黑光）
- 历史兼容名：BKLT 黑光、ONYX-OVERRIDE
- 定位：本地优先 AI Agent 自动化可视化工作台
- 技术栈：Electron + React/Vite + FastAPI + SQLite
- 默认后端：`http://127.0.0.1:8000`
- 本地模型网关：Ollama 或 OpenAI-compatible `/v1` 网关

## 常用入口

- 桌面启动：`launcher/START_APP.bat`
- 统一启动：`python start.py`
- 开发模式：`python start.py dev`
- 仅后端：`python start.py backend`
- 手机访问：`python start.py mobile`

## 修改前先做

1. 查看 `git status` 和 `git diff`。
2. 特别注意不要覆盖用户本地半成品：`backend/context_pack.py`、`backend/memory_store.py`。
3. 不要提交 `.env`、数据库、`node_modules`、`outputs`、`frontend/build`、日志、个人运行记录或临时文件。
4. 若需要删除大量文件、暴露密钥、登录授权、付款、发布外部平台、系统级权限或不可逆操作，必须先让用户确认。

## 验证命令

按改动范围选择最小但真实的验证：

```bash
# Python 语法/后端核心
python -m py_compile backend/main.py backend/agent.py backend/automation_runner.py backend/tool_registry.py

# 后端测试
pytest backend/tests

# 前端构建
npm run build --prefix frontend

# 应用自检（Windows PowerShell）
powershell -ExecutionPolicy Bypass -File scripts/test-app.ps1
```

如果只能改文档，也要在最终汇报里明确“本次未改运行时代码，因此未跑构建/测试”。

## 架构方向

优先把项目做成可视化 Agent Control Plane：

- Agent 执行时间线：thinking → tool_call → tool_result → final_answer
- 工具注册表：分组、参数 schema、风险等级、确认机制
- 自动化维护：项目健康检查、前端构建、后端编译、GitHub 同步状态
- 记忆系统：SQLite + 技能包 + 上下文压缩 + 记忆树
- 手机端入口：局域网/Tailscale 地址、二维码、token 登录状态
- 互操作：MCP、A2A、OpenAI-compatible 模型网关、Ollama 本地模型

## 代码风格

- Python：保持小函数、明确异常、API 返回 `{ok: bool, ...}` 风格。
- 前端：React 组件要能在暗色科技 UI 中使用，优先复用已有 CSS 类。
- 安全：危险工具必须有风险分层和用户确认入口。
- 本地优先：不要把用户文件、数据库或运行日志上传到第三方。

## Agent 对标重点

更新 Agent 能力时优先参考这些方向，而不是盲目复制外部仓库：

- LangGraph：持久化、可恢复执行、人类中断、事件流
- OpenAI Agents SDK：handoff、guardrails、tracing、sandbox/session
- Google ADK：图工作流、上下文管理、A2A、部署/观测
- CrewAI：crews/flows、触发器、RBAC、运行监控
- AutoGen：多 Agent 会话、Studio 可视化、Docker 执行器
- Claude Code/Copilot/Devin/Cursor：项目级指令、技能、hooks、PR/分支工作流、后台任务、可审计产物

## 汇报格式

完成后简短汇报：

1. 改了什么
2. 真实跑了什么验证
3. 结果是什么
4. 还剩什么风险或下一步
