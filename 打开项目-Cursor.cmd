@echo off
REM 用 Cursor 打开本项目文件夹（避免嵌套 workspace 路径错误）
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
start "" cursor "%ROOT%"
