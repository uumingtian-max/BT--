@echo off
call "%~dp0_project_root.bat"
chcp 65001 >nul
title BT（黑光）— 首次安装

echo ========================================
echo   BT（黑光）首次安装
echo ========================================
echo.

where node >nul 2>&1 || (echo 请安装 Node.js 18+ & pause & exit /b 1)

echo [1/3] Electron 依赖…
node "%PROJECT_ROOT%scripts\npm.cjs" install || goto fail

echo [2/3] 前端依赖…
node "%PROJECT_ROOT%scripts\npm.cjs" install --prefix frontend || goto fail

if not exist "backend\.env" (
  echo [3/3] 创建 backend\.env …
  copy /Y "backend\.env.local-llamacpp.example" "backend\.env" >nul 2>&1
  if not exist "backend\.env" copy /Y "backend\.env.example" "backend\.env" >nul
) else (
  echo [3/3] backend\.env 已存在
)

if not exist "frontend\build\index.html" (
  node "%PROJECT_ROOT%scripts\npm.cjs" run build --prefix frontend
)

echo.
echo 完成。请运行 launcher\START_APP.bat
pause
exit /b 0

:fail
echo 安装失败
pause
exit /b 1
