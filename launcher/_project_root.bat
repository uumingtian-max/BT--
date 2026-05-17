@echo off
set "PROJECT_ROOT=%~dp0..\"
for %%I in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fI\"
cd /d "%PROJECT_ROOT%"
