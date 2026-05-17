@echo off
setlocal
cd /d "%~dp0"
python scripts\prepare-gemma-evolution-dataset.py %*
pause
