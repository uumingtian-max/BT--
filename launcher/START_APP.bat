@echo off
call "%~dp0_project_root.bat"
chcp 65001 >nul
title BT Heiguang
if not defined PLAYWRIGHT_BROWSERS_PATH set "PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright"

if not exist "backend\.env" (
  echo First run: copying backend\.env.local-llamacpp.example
  copy /Y "backend\.env.local-llamacpp.example" "backend\.env" >nul 2>&1
  if not exist "backend\.env" copy /Y "backend\.env.example" "backend\.env" >nul
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%scripts\ensure-runtime.ps1" >nul 2>&1

where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js was not found.
  pause
  exit /b 1
)

if not exist "node_modules\" (
  echo Installing Electron dependencies...
  node "%PROJECT_ROOT%scripts\npm.cjs" install
)

if not exist "frontend\build\index.html" (
  echo Building frontend...
  node "%PROJECT_ROOT%scripts\npm.cjs" run build --prefix frontend
)

if not exist "electron\icon-1024.png" (
  python "%PROJECT_ROOT%scripts\build-branding.py" 2>nul
)

set SKIP_OLLAMA=
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; if(Test-Path 'backend\.env'){ $ok = Select-String -LiteralPath 'backend\.env' -Pattern '^\s*LLM_BACKEND\s*=\s*openai_compatible\s*$' -Quiet }; exit ([int](-not $ok))"
if errorlevel 1 (
  echo Checking Ollama...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%scripts\ensure-ollama.ps1"
) else (
  set SKIP_OLLAMA=1
  echo Checking llama.cpp gateway...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%scripts\ensure-llama-cpp.ps1"
  if errorlevel 1 (
    echo [BT] Model gateway is not ready. See logs\llama-server.log
    pause
    exit /b 1
  )
)

set NODE_ENV=production
node "%PROJECT_ROOT%scripts\npm.cjs" run electron
exit /b %errorlevel%
