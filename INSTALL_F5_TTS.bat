@echo off
setlocal
cd /d "%~dp0"
echo.
echo [ONYX] Installing F5-TTS into isolated .venv-f5 ...
echo [ONYX] This can take a while because torch/model dependencies are large.
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\install-f5-tts.ps1"
pause
