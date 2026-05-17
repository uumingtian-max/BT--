@echo off
setlocal
cd /d "%~dp0"
echo.
echo [ONYX] Configure secure remote mobile access token
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\setup-remote-mobile.ps1"
pause
