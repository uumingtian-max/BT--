@echo off
chcp 65001 >nul
title vLLM - Nemotron 3 Nano (WSL)
cd /d "%~dp0.."
echo.
echo [BKLT] 启动 Nemotron-3-Nano OpenAI-compatible 网关...
echo [BKLT] 地址：http://127.0.0.1:8001/v1/models
echo [BKLT] 模型目录：D:\models\NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4
echo.
wsl bash -lc "MODEL_DIR=/mnt/d/models/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 PORT=8001 bash /mnt/c/Users/ROG/Desktop/ai-agent-project/scripts/vllm-serve-nemotron3-nano-wsl.sh"
pause
