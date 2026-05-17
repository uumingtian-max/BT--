# launcher — 一键启动

Windows 下从这里启动 BT（黑光）。

常用：

- `START_APP.bat` — 桌面应用（自动拉 llama.cpp / Ollama）
- `INSTALL_FIRST_RUN.bat` — 首次安装 Node / Python 依赖
- `Launch-BT-Heiguang.vbs` — 做桌面快捷方式（无黑框）
- `打开本机Gemma模型.cmd` — 只起 llama-server（:8001）
- `打开AI Agent.cmd` — 同 START_APP

其它：`START_DEV.bat` 开发模式；`install/`、`train/`、`misc/` 为可选脚本；`compat/` 为旧版快捷方式兼容。

所有 bat/cmd 会先执行 `_project_root.bat` 切换到项目根目录。
