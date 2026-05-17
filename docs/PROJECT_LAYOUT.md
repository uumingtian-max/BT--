# 项目目录（BT 黑光）

```text
ai-agent-project/
├── backend/          # 后端核心（FastAPI、Agent、工具、.env）
├── frontend/         # React 界面
├── electron/         # 桌面壳（package.json 依赖，与 frontend 配套）
├── launcher/         # 一键启动脚本（bat / cmd / vbs）
├── docs/             # 文档
├── scripts/          # 工具脚本（安装、诊断、打包、模型）
├── assets/           # 静态资源与品牌素材
├── data/             # 本机数据（知识库等，gitignore）
├── start.py          # 统一启动入口（跨平台）
├── README.md
├── .env.example      # 配置说明（真配置在 backend/.env）
├── requirements.txt  # Python 依赖（指向 backend/requirements.txt）
└── package.json      # Electron / Node 工程元数据
```

## 怎么启动

- Windows 双击：`launcher/START_APP.bat` 或 `launcher/Launch-BT-Heiguang.vbs`
- 命令行：`python start.py`（等同桌面应用）、`python start.py dev`（开发）

## 归档

`archive/_onyx_pack_desktop/` — 原桌面 `_onyx_pack`；`archive/_onyx_pack_v1.1.0/` — 旧快照。见 `archive/README.md`。

## 运行时目录（不进 Git）

`node_modules/`、`outputs/`、`logs/`、`data/`

## 文档

- 多模态 llama.cpp：`docs/setup/LLAMA_CPP.md`
- Docker 部署：`docs/deploy/docker-compose.yml`
