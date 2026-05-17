@echo off
chcp 65001 >nul
title ONYX - OpenAI/Codex Provider Setup
cd /d "%~dp0"

echo.
echo === ONYX OpenAI/Codex Provider Setup ===
echo 这个脚本会把 backend\.env 切到 OpenAI-compatible 模式。
echo 会自动备份原配置，API key 只写入本机 backend\.env。
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\configure-openai-provider.ps1"
echo.
echo 配置完成后，请重新打开 ONYX-OVERRIDE。
pause
