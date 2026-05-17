@echo off
chcp 65001 >nul
title ONYX-OVERRIDE (实验 — OpenAI 兼容网关 / vLLM)
cd /d "%~dp0"
if not defined PLAYWRIGHT_BROWSERS_PATH set "PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright"

echo.
echo 【说明】此为实验入口：依赖本机 8001 上的 vLLM 等网关。Windows GPU 上极不稳定。
echo         日常使用请 START_APP.bat + Ollama（GPU 直出，见 backend\.env.example）。
echo.

if not exist "backend\.env" (
  echo 使用网关模式示例配置…
  copy /Y "backend\.env.local-gemma4.example" "backend\.env" >nul
)

echo 检查本机 vLLM / OpenAI 兼容网关 (端口 8001)…
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ok=$false; foreach($u in @('http://127.0.0.1:8001/v1/models','http://127.0.0.1:8001/health')){ try { $r=Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 5; if($r.StatusCode -eq 200){ $ok=$true; break } } catch {} }; exit ([int](-not $ok))"
if errorlevel 1 (
  echo [提示] 网关未就绪（8001）。请先在本机或其它 GPU 机上启动兼容服务，
  echo        或改用稳定方案：START_APP.bat + Ollama。
  pause
  exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 Node.js
  pause
  exit /b 1
)

if not exist "node_modules\" node "%~dp0scripts\npm.cjs" install
if not exist "frontend\build\index.html" node "%~dp0scripts\npm.cjs" run build --prefix frontend

echo 跳过 Ollama，使用本机 vLLM + backend\.env
set NODE_ENV=production
set SKIP_OLLAMA=1
node "%~dp0scripts\npm.cjs" run electron
exit /b %errorlevel%
