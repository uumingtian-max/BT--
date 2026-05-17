@echo off
chcp 65001 >nul
title vLLM - Gemma 4 (实验性 / WSL)
cd /d "%~dp0.."
echo.
echo [提示] Windows 上官方 vLLM 无稳定 GPU 支持；本脚本走 WSL，易踩坑。
echo        日常推荐：用 Ollama + GPU，backend\.env 选 LLM_BACKEND=ollama
echo        详见 backend\.env.local-gemma4.example 顶部说明。
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ensure-vllm.ps1" -Start -ApplyEnv -WaitSec 900
pause
