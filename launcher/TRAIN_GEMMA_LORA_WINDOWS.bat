@echo off
call "%~dp0..\_project_root.bat"
setlocal
set GEMMA_BASE_MODEL=D:\models\Gemma-4-26B-A4B-NVFP4
C:\Users\ROG\miniconda3\envs\quant\python.exe scripts\train-gemma-lora-windows.py %*
pause
