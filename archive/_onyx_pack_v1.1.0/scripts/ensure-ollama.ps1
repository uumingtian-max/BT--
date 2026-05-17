# 确保 Ollama 已启动并就绪（START_APP / 桌面快捷方式调用）
$ErrorActionPreference = "SilentlyContinue"
$hostUrl = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST.TrimEnd('/') } else { "http://127.0.0.1:11434" }

function Test-Ollama {
    try {
        $r = Invoke-WebRequest -Uri "$hostUrl/api/tags" -UseBasicParsing -TimeoutSec 3
        return $r.StatusCode -eq 200
    } catch { return $false }
}

if (Test-Ollama) { exit 0 }

$ollama = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
if (-not (Test-Path $ollama)) { $ollama = (Get-Command ollama -ErrorAction SilentlyContinue).Source }
if (-not $ollama) {
    Write-Host "[ONYX] 未找到 Ollama，请先安装 https://ollama.com 后再启动本应用。" -ForegroundColor Yellow
    exit 1
}

Write-Host "[ONYX] 正在启动 Ollama…" -ForegroundColor Cyan
Start-Process -FilePath $ollama -ArgumentList "serve" -WindowStyle Hidden

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Ollama) { exit 0 }
}

Write-Host "[ONYX] Ollama 启动超时，模型可能无法回复。请手动运行: ollama serve" -ForegroundColor Yellow
exit 1
