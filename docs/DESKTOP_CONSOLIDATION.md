# 桌面项目合并说明

**唯一工作目录：** `C:\Users\ROG\Desktop\ai-agent-project`（**BT（黑光）**）

## 曾有的两个来源

- **主项目**：`Desktop\ai-agent-project` — 日常只用这个。
- **旧便携包**：桌面 `_onyx_pack` 里的副本 — 已整包移到 `archive\_onyx_pack_desktop\`，不要再从那里启动。

更早的精简快照在 `archive\_onyx_pack_v1.1.0\`（仅供参考，不是日常目录）。

## 推荐入口（均在 launcher 目录）

- 桌面应用：`launcher\START_APP.bat` 或 `launcher\Launch-BT-Heiguang.vbs`
- 只起 llama.cpp：`launcher\打开本机Gemma模型.cmd`
- 开发模式：`launcher\START_DEV.bat` 或 `python start.py dev`
- 首次安装：`launcher\INSTALL_FIRST_RUN.bat`

## 目录一览

```text
ai-agent-project/
├── backend/
├── frontend/
├── electron/
├── launcher/         # 所有 bat / cmd / vbs 启动脚本
├── docs/
├── scripts/          # 工具脚本（不含启动 bat）
├── assets/
├── data/
├── archive/
├── outputs/
├── start.py
├── README.md
├── .env.example
└── requirements.txt
```

## 相关归档

- `docs/archive/MERGE_REPORT.md`
- `docs/archive/FIX_APPLIED_FROM_ZIP.md`
- `archive/_onyx_pack_desktop/` — 原桌面 `_onyx_pack`
- `archive/_onyx_pack_v1.1.0/` — 旧版精简快照
