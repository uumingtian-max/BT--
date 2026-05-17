@echo off
call "%~dp0..\_project_root.bat"
setlocal
python scripts\prepare-gemma-evolution-dataset.py %*
pause
