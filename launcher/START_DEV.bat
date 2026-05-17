@echo off
call "%~dp0_project_root.bat"
chcp 65001 >nul
title BT（黑光）- DEV
set "NPM_CONFIG_DEVDIR="
set "npm_config_devdir="
if not defined PLAYWRIGHT_BROWSERS_PATH set "PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright"

if not exist "backend\.env" copy /Y "backend\.env.example" "backend\.env" >nul

where node >nul 2>&1 || (echo 未找到 Node.js & pause & exit /b 1)
if not exist "node_modules\" node "%PROJECT_ROOT%scripts\npm.cjs" install
if not exist "frontend\node_modules\" node "%PROJECT_ROOT%scripts\npm.cjs" install --prefix frontend

start "BT Backend" cmd /k "%PROJECT_ROOT%scripts\start-backend.cmd"
timeout /t 2 /nobreak >nul
start "BT Frontend" cmd /k "cd /d %PROJECT_ROOT%frontend && node %PROJECT_ROOT%scripts\npm.cjs start"
timeout /t 15 /nobreak >nul
set NODE_ENV=development
cd /d "%PROJECT_ROOT%"
npx --yes electron .
