@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 正在打开小涵记忆相关配置...
start "" notepad "%~dp0backend\chat.py"
start "" notepad "%~dp0backend\.env"
start "" notepad "%~dp0scripts\seed-identity-memory.py"

echo.
echo 已打开：
echo - backend\chat.py       小涵系统身份提示
echo - backend\.env          长上下文/记忆窗口配置
echo - scripts\seed-identity-memory.py  长期身份记忆种子
echo.
echo 写完保存后，回到这里告诉 Codex：我写好了，帮我拉一下。
pause
