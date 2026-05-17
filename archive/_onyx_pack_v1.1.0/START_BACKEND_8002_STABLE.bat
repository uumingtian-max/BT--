@echo off
chcp 65001 >nul
cd /d "%~dp0backend"
set "UVICORN_RELOAD=0"
set "BACKEND_PORT=8002"
set "PLAYWRIGHT_BROWSERS_PATH=%LOCALAPPDATA%\ms-playwright"
set "PY=%USERPROFILE%\miniconda3\envs\quant\python.exe"
if not exist "%PY%" set "PY=%USERPROFILE%\miniconda3\python.exe"
"%PY%" main.py >> "%~dp0logs\backend-8002-stable.out.log" 2>> "%~dp0logs\backend-8002-stable.err.log"
