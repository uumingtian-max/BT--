@echo off
chcp 65001 >nul
title BKLT 黑光
cd /d "%~dp0"
if not defined PLAYWRIGHT_BROWSERS_PATH set "PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright"

if not exist "backend\.env" (
  echo 首次运行：复制 backend\.env.example
  copy /Y "backend\.env.example" "backend\.env" >nul
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ensure-runtime.ps1" >nul 2>&1

where node >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 Node.js，请先安装 Node。
  pause
  exit /b 1
)

if not exist "node_modules\" (
  echo 安装 Electron 依赖…
  node "%~dp0scripts\npm.cjs" install
)

if not exist "frontend\build\index.html" (
  echo 首次启动：构建前端界面…
  node "%~dp0scripts\npm.cjs" run build --prefix frontend
)

if not exist "electron\icon-1024.png" (
  echo 生成高清图标…
  "%USERPROFILE%\miniconda3\python.exe" "%~dp0scripts\build-branding.py" 2>nul
  if not exist "electron\icon-1024.png" python "%~dp0scripts\build-branding.py"
)

REM 若 backend\.env 已配置 OpenAI 兼容网关（vLLM / NIM 等），跳过 Ollama 启动与自检
set SKIP_OLLAMA=
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; if(Test-Path 'backend\.env'){ $ok = Select-String -LiteralPath 'backend\.env' -Pattern '^\s*LLM_BACKEND\s*=\s*openai_compatible\s*$' -Quiet }; exit ([int](-not $ok))"
if errorlevel 1 (
  echo 检查 Ollama（模型服务）…
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ensure-ollama.ps1"
) else (
  echo [BKLT] LLM_BACKEND=openai_compatible — 跳过 Ollama；请保持 OPENAI_BASE_URL 网关已就绪（如 vLLM :8001）。
  set SKIP_OLLAMA=1
)

set NODE_ENV=production
node "%~dp0scripts\npm.cjs" run electron
exit /b %errorlevel%
