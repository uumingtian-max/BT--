@echo off
REM 兼容入口：历史快捷方式可能仍调用 START.bat，统一转发到官方 START_APP.bat
cd /d "%~dp0"
call "%~dp0START_APP.bat"
exit /b %errorlevel%
