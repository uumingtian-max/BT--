@echo off
chcp 65001 >nul
title ONYX Mobile Tailscale 8002

cd /d "%~dp0backend"

if not defined BACKEND_PORT set "BACKEND_PORT=8002"

if not defined PLAYWRIGHT_BROWSERS_PATH set "PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright"

set "PY="
if defined AI_AGENT_PYTHON (
  set "PY=%AI_AGENT_PYTHON%"
  goto run
)

if exist "%USERPROFILE%\miniconda3\envs\quant\python.exe" (
  set "PY=%USERPROFILE%\miniconda3\envs\quant\python.exe"
  goto run
)

if exist "%USERPROFILE%\miniconda3\python.exe" (
  set "PY=%USERPROFILE%\miniconda3\python.exe"
  goto run
)

set "PY=python"

:run
echo.
echo ONYX Mobile Tailscale backend
echo.
echo Python: %PY%
echo Listen: 0.0.0.0:%BACKEND_PORT%
echo Phone URL: http://^<本机Tailscale IP^>:%BACKEND_PORT%/mobile/
echo.
echo Keep this window open.
echo.

if "%PY%"=="python" (
  python -m uvicorn main:app --host 0.0.0.0 --port %BACKEND_PORT%
) else (
  "%PY%" -m uvicorn main:app --host 0.0.0.0 --port %BACKEND_PORT%
)

echo.
echo Backend exited. If there is an error above, send me a screenshot.
pause
