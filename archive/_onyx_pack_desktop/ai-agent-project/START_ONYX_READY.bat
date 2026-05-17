@echo off
chcp 65001 >nul
title ONYX 一键就绪
cd /d "%~dp0"
if not defined PLAYWRIGHT_BROWSERS_PATH set "PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright"

echo [1/4] 检查 Ollama...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ensure-ollama.ps1"
if errorlevel 1 (
  echo Ollama 未就绪，请先安装 https://ollama.com
  pause
  exit /b 1
)

echo [2/4] 重启后端 8000（加载 .env + 86 技能）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
  taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul
start "ONYX-Backend" cmd /c "%~dp0scripts\start-backend.cmd"
echo 等待后端启动...
powershell -NoProfile -Command "$ok=$false; 1..45 | %% { try { if ((Invoke-WebRequest 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { $ok=$true; break } } catch {}; Start-Sleep 1 }; if (-not $ok) { exit 1 }"
if errorlevel 1 (
  echo 后端启动超时，请查看 ONYX-Backend 窗口报错
  pause
  exit /b 1
)

echo [3/4] 习惯体检 + 技能库...
powershell -NoProfile -Command "Invoke-RestMethod -Method POST -Uri 'http://127.0.0.1:8000/meta/habit/run' -TimeoutSec 120 | Out-Null"
powershell -NoProfile -Command "$d=Invoke-RestMethod 'http://127.0.0.1:8000/meta/doctor'; $s=Invoke-RestMethod 'http://127.0.0.1:8000/meta/skills'; Write-Host ('体检: ok=' + $d.ok + ' failed=' + $d.failed_count); Write-Host ('技能: ' + $s.count + ' 条')"

echo [4/4] 启动桌面 ONYX...
if not exist "frontend\build\index.html" (
  echo 构建前端...
  node "%~dp0scripts\npm.cjs" run build --prefix frontend
)
set NODE_ENV=production
set SKIP_OLLAMA=1
start "" node "%~dp0scripts\npm.cjs" run electron
echo.
echo 已就绪。模型: qwen3:14b（Ollama）。升级 vLLM+Gemma: 见 backend\.env.local-gemma4.example
exit /b 0
