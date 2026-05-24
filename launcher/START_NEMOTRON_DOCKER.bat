@echo off
cd /d "%~dp0.."
echo [0/4] 释放 GPU：卸载 Ollama 已加载模型（避免与 Nemotron 抢 24GB 显存）...
ollama ps 2>nul | findstr /R "." >nul && (
  for /f "tokens=1" %%m in ('ollama ps -q 2^>nul') do ollama stop %%m 2>nul
)
echo [1/4] 生成补丁 config.json ...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\patch-nemotron-config.ps1
if errorlevel 1 exit /b 1
echo [2/4] 构建镜像并启动（含 librosa，首次较慢）...
docker compose -f docker-compose.nemotron.yml up -d --build
if errorlevel 1 exit /b 1
echo [3/4] 等待就绪（加载约 3-8 分钟，另开窗口可看日志）...
timeout /t 90 /nobreak >nul
powershell -NoProfile -Command "try { (Invoke-WebRequest 'http://127.0.0.1:8001/health' -TimeoutSec 5).Content } catch { '尚未就绪: ' + $_.Exception.Message }"
echo [4/4] 查看日志: docker logs -f bt-nemotron-sglang
echo 健康检查: http://127.0.0.1:8001/health
pause
