@echo off
chcp 65001 >nul
title ONYX-OVERRIDE — 首次安装依赖
cd /d "%~dp0"

echo ========================================
echo   ONYX-OVERRIDE 首次安装
echo ========================================
echo.

where node >nul 2>&1
if errorlevel 1 (
  echo [错误] 未安装 Node.js。请从 https://nodejs.org 安装 LTS 后重试。
  pause
  exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
  echo [警告] 未在 PATH 中找到 python，后端可能无法启动。
  echo        请安装 Python 3.10+ 或 Miniconda。
)

echo [1/3] 安装 Electron 依赖…
node "%~dp0scripts\npm.cjs" install
if errorlevel 1 goto fail

echo [2/3] 安装前端依赖…
node "%~dp0scripts\npm.cjs" install --prefix frontend
if errorlevel 1 goto fail

if not exist "backend\.env" (
  echo [3/3] 创建 backend\.env …
  copy /Y "backend\.env.example" "backend\.env" >nul
) else (
  echo [3/3] backend\.env 已存在，跳过
)

if not exist "frontend\build\index.html" (
  echo 构建前端界面…
  node "%~dp0scripts\npm.cjs" run build --prefix frontend
)

echo.
echo 安装完成。请运行 START_APP.bat 或双击桌面 ONYX-OVERRIDE 快捷方式。
echo 还需安装 Ollama 并拉取模型，例如: ollama pull qwen3:14b
echo.
pause
exit /b 0

:fail
echo.
echo 安装失败，请检查网络与 Node 版本后重试。
pause
exit /b 1
