# 黑光当前本地项目地图

更新时间：2026-05-27

## 当前主线

黑光当前主项目是：

`C:\Users\ROG\Desktop\ai-agent-project`

当前只保留一个清晰主线：本地桌面 Agent + FastAPI 后端 + React/Electron 前端 + SGLang/Nemotron 本地模型路由 + 27 个变现专家席。

## 日常只看这些

| 路径 | 用途 |
|---|---|
| `README.md` | 项目总说明 |
| `docs/CURRENT_LOCAL_MAP.md` | 当前本地项目地图 |
| `docs/PROJECT_LAYOUT.md` | 目录职责说明 |
| `backend/` | FastAPI、Agent、工具、记忆、模型路由 |
| `frontend/src/` | React 前端 |
| `electron/` | 桌面壳 |
| `launcher/` | 一键启动 |
| `scripts/` | 本地脚本、排障、构建、模型辅助 |
| `docs/` | 架构、设计、部署、模型说明 |
| `meta/` | 专家席/能力元信息 |

## 当前 staged 主线变更

这批是当前保留并已验证的主线：

- `backend/expert_monetize_27.py`：27 个变现/自动化专家席。
- `backend/expert_roles.py`：核心 11 专家 + 27 变现专家统一 manifest 和路由。
- `backend/execution_kernel.py`：执行内核可按任务插入变现专家席。
- `backend/llm_dual_route.py`：GPU/SGLang 与 API 双引擎路由。
- `backend/.env.dual-engine.example`：双引擎配置示例。
- `backend/tests/test_expert_monetize_27.py`：变现专家路由测试。
- `docs/setup/SGLANG_NEMOTRON_TASKS.md`：Nemotron + SGLang 任务说明。
- `meta/expert-roles-monetize-27.md`：变现专家表。

## 已隔离的无关内容

其它项目上下文、Sophia/MemRL/艾宾浩斯实验、额外前端绿点、SadTalker 临时接口、外来规则等，已统一移入：

`archive/scope-clean-current-20260527/`

里面包含：

- `untracked-files/`：原未跟踪文件的完整归档。
- `generated-runtime/`：外来实验生成的本地数据。
- `unstaged-before-clean.patch`：清理 tracked 文件前的未暂存 diff 备份。
- `untracked-before-clean.txt`：原未跟踪文件列表。

## 不要当工作区的目录

| 路径 | 原因 |
|---|---|
| `archive/` | 历史和隔离归档，只查不改 |
| `outputs/` | 运行产物 |
| `data/` | 本地数据和知识库 |
| `vendor/` | 外部参考仓 |
| `SadTalker/` | 第三方数字人仓，权重未齐时不要当主线 |
| `node_modules/` / `frontend/node_modules/` | 依赖目录 |
| `.venv-f5/` | 语音环境 |

## 当前验证命令

```powershell
python -m py_compile backend\expert_monetize_27.py backend\expert_roles.py backend\execution_kernel.py backend\llm_dual_route.py backend\tests\test_expert_monetize_27.py
python -m pytest backend\tests\test_expert_monetize_27.py backend\tests\test_llm_dual_route.py backend\tests\test_tool_registry.py -q
node scripts\npm.cjs run build --prefix frontend
git diff --cached --check
```
