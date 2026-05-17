@echo off
chcp 65001 >nul
title ONYX-OVERRIDE - DEV
set "NPM_CONFIG_DEVDIR="
set "npm_config_devdir="
cd /d "%~dp0"
if not defined PLAYWRIGHT_BROWSERS_PATH set "PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright"

if not exist "backend\.env" (
  echo First run: copying backend\.env.example to backend\.env
  copy /Y "backend\.env.example" "backend\.env" >nul
)

where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js not found in PATH.
  pause
  exit /b 1
)

if not exist "node_modules\" (
  echo Installing root dependencies ^(Electron^)...
  node "%~dp0scripts\npm.cjs" install
)
if not exist "frontend\node_modules\" (
  echo Installing frontend dependencies...
  pushd frontend
  node "%~dp0scripts\npm.cjs" install
  popd
)

curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
  start /B ollama serve
  timeout /t 3 /nobreak >nul
)

start "AI Agent Backend" cmd /k "%~dp0scripts\start-backend.cmd"
timeout /t 2 /nobreak >nul

start "AI Agent Frontend" cmd /k "cd /d %~dp0frontend && node %~dp0scripts\npm.cjs start"

echo Waiting for React dev server...
timeout /t 15 /nobreak >nul

set NODE_ENV=development
npx --yes electron .
