@echo off
cd /d "%~dp0"

if exist "%~dp0START_APP.bat" (
  call "%~dp0START_APP.bat"
  exit /b %errorlevel%
)

if exist "%~dp0launcher\START_APP.bat" (
  call "%~dp0launcher\START_APP.bat"
  exit /b %errorlevel%
)

if exist "%~dp0scripts\launch-agent.ps1" (
  powershell -ExecutionPolicy Bypass -File "%~dp0scripts\launch-agent.ps1"
  exit /b %errorlevel%
)

if exist "%~dp0start.py" (
  python "%~dp0start.py"
  exit /b %errorlevel%
)

echo [BKLT] No valid launcher found.
pause
exit /b 1
