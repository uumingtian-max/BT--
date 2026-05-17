# 项目目录（BT 黑光）

按职责分类的顶层结构（日常开发只关心 **核心** 与 **启动** 几类即可）。

```text
ai-agent-project/
├── backend/          FastAPI + Agent + 技能包（agent_skills/）
├── frontend/         React UI
├── electron/         桌面壳（splash.html、启动图标）
├── launcher/         一键启动（START_APP.bat 等）
├── docs/             文档（含 deploy/docker-compose.yml）
├── scripts/          工具脚本（安装、诊断、外仓 sync、llama）
├── assets/           品牌资源
├── data/             本机数据（知识库等，不进 Git）
├── vendor/           外仓对照（agency-agents、gstack，不进 Git 克隆体）
├── archive/          历史快照（勿作日常目录）
├── .cursor/          Cursor 规则（写代码用，可选）
├── start.py          统一启动入口
├── README.md
├── .env.example      配置说明（真配置在 backend/.env）
├── requirements.txt  # → backend/requirements.txt
└── package.json      Electron / Node 元数据
```

## 分类说明

| 分类 | 目录 / 文件 | 做什么 | 日常要不要碰 |
|------|-------------|--------|--------------|
| **后端** | `backend/` | API、Agent、工具、记忆、调度；技能 `backend/agent_skills/*.md`；配置 `backend/.env` | 常改 |
| **前端** | `frontend/` | React 界面；构建产物 `frontend/build/`（不进 Git） | 改 UI 时 |
| **桌面壳** | `electron/` | Electron 窗口、splash、与前端打包联动 | 改壳子时 |
| **启动** | `launcher/`、`start.py` | 双击 bat/vbs 或 `python start.py` | 启动用 |
| **文档** | `docs/` | 架构、部署、LLAMA_CPP、维护基线 | 查说明时 |
| **脚本** | `scripts/` | `ensure-llama-cpp.ps1`、`sync-bt-vendor-repos.ps1` 等 | 装环境/排障时 |
| **品牌** | `assets/` | 图标、manifest 素材 | 换品牌时 |
| **本机数据** | `data/` | 知识库、本地 DB 等（gitignore） | 运行时自动写 |
| **外仓对照** | `vendor/` | 仅 manifest + README 进 Git；克隆在 `vendor/*/` | 对照更新技能时 |
| **归档** | `archive/` | 旧 ONYX 包等快照 | **不要**当工作目录 |
| **IDE** | `.cursor/rules/` | Cursor 写代码规则（如 `agency-*.mdc`） | 在 Cursor 里开发时 |
| **根入口** | `README.md`、`requirements.txt`、`.env.example` | 说明与依赖入口 | 首次克隆时 |

## 不进 Git 的常见路径

`node_modules/`、`frontend/build/`、`logs/`、`outputs/`、`data/*.db`、`backend/.env`、`vendor/agency-agents/`、`vendor/gstack/`

## 怎么启动

- Windows：`launcher/START_APP.bat` 或 `launcher/Launch-BT-Heiguang.vbs`
- 命令行：`python start.py`（桌面）、`python start.py dev`（开发）
- 根目录 `START_APP.bat` 仅转发到 `launcher/`（兼容旧快捷方式）

## 相关文档

- 维护基线：`docs/BKLT_BLACKLIGHT_MAINTENANCE.md`
- 多模态 / llama.cpp：`docs/setup/LLAMA_CPP.md`
- Docker：`docs/deploy/docker-compose.yml`
- 外仓对照：`vendor/README.md`
- 启动器说明：`launcher/README.md`
