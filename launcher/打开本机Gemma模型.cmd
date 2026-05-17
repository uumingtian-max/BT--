@echo off
call "%~dp0_project_root.bat"
chcp 65001 >nul
title 启动 llama.cpp 多模态 Gemma4
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%scripts\ensure-llama-cpp.ps1"
if errorlevel 1 (
  echo 失败，见 logs\llama-server.log
  pause
  exit /b 1
)
echo 网关已就绪：http://127.0.0.1:8001/v1
echo 再运行 launcher\START_APP.bat 打开应用。
pause
