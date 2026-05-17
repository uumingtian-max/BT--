@echo off
chcp 65001 >nul
cd /d "%~dp0..\backend"
if not defined PLAYWRIGHT_BROWSERS_PATH set "PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright"

set "PY="
if defined AI_AGENT_PYTHON (
  set "PY=%AI_AGENT_PYTHON%"
  goto :run
)
if exist "%USERPROFILE%\miniconda3\envs\quant\python.exe" (
  set "PY=%USERPROFILE%\miniconda3\envs\quant\python.exe"
  goto :run
)
if exist "%USERPROFILE%\miniconda3\python.exe" (
  set "PY=%USERPROFILE%\miniconda3\python.exe"
  goto :run
)
set "PY=python"

:run
echo [后端] Python: %PY%
echo [后端] 目录: %CD%
echo.

if "%PY%"=="python" (
  python -m uvicorn main:app --host 0.0.0.0 --port 8000
) else (
  "%PY%" -m uvicorn main:app --host 0.0.0.0 --port 8000
)

if errorlevel 1 (
  echo.
  echo 启动失败。在此目录执行: pip install -r requirements.txt
  echo 或设置环境变量 AI_AGENT_PYTHON=你的 python.exe 完整路径
  echo.
  pause
)
exit /b %errorlevel%
