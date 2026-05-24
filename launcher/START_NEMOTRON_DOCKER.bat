@echo off
cd /d "%~dp0.."
echo [1/3] 生成补丁 config.json ...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\patch-nemotron-config.ps1
if errorlevel 1 exit /b 1
echo [2/3] 构建镜像并启动（含 librosa，首次较慢）...
docker compose -f docker-compose.nemotron.yml up -d --build
if errorlevel 1 exit /b 1
echo [3/3] 查看日志: docker logs -f bt-nemotron-sglang
echo 健康检查: http://127.0.0.1:8001/health
pause
