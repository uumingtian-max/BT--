@echo off
chcp 65001 >nul
title AI Agent 生产模式
echo.
echo 说明：日常请用「打开AI Agent.cmd」或桌面同名快捷方式 ^（开发模式^）。
echo 本脚本为「构建前端 + Electron」，无 React 热更新。
echo.
call "%~dp0START.bat"
