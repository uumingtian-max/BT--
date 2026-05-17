@echo off
chcp 65001 >nul
title ONYX-OVERRIDE Mobile Backend
cd /d "%~dp0"

echo.
echo ONYX-OVERRIDE 手机访问模式
echo.
echo 请让手机和电脑连接同一个 Wi-Fi，然后在手机浏览器打开：
echo.
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
  for /f "tokens=* delims= " %%B in ("%%A") do echo   http://%%B:8002/mobile/
)
echo.
echo 如果打不开，请允许 Windows 防火墙放行 Python / 端口 8002（专用网络；可在 backend/.env 改 BACKEND_PORT）。
echo 手机端聊天会连接电脑上的大模型；真人音色可另开 START_F5_TTS.bat。
echo 下面开始启动后端；这个窗口不要关闭。
echo.

call "%~dp0scripts\start-backend.cmd"
