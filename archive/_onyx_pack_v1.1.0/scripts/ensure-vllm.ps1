# 确保 vLLM (Gemma4) 在 8001 就绪；Windows 走 WSL，不用 Ollama
param(
    [int]$Port = 8001,
    [int]$WaitSec = 900,
    [switch]$Start,
    [switch]$ApplyEnv
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envGemma = Join-Path $root "backend\.env.local-gemma4.example"
$envFile = Join-Path $root "backend\.env"
$logDir = Join-Path $root "logs"
function ConvertTo-WslPath([string]$WinPath) {
    $p = $WinPath -replace '\\', '/'
    if ($p -match '^([A-Za-z]):(.*)$') {
        return "/mnt/$($Matches[1].ToLower())$($Matches[2])"
    }
    return $p
}
$wslScript = "$(ConvertTo-WslPath $root)/scripts/vllm-serve-wsl.sh"
$wslLog = "/tmp/onyx-vllm.log"

function Test-VllmUp {
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 5
        return $r.StatusCode -eq 200
    } catch { return $false }
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if ($ApplyEnv -and (Test-Path $envGemma)) {
    Copy-Item -Force $envGemma $envFile
    Write-Host "[vLLM] 已应用 backend\.env (Gemma4 + openai_compatible)" -ForegroundColor DarkGray
}

if (Test-VllmUp) {
    Write-Host "[vLLM] 已在 http://127.0.0.1:$Port 运行" -ForegroundColor Green
    exit 0
}

if (-not $Start) {
    Write-Host "[vLLM] 未运行。请加 -Start 或运行 scripts\START_VLLM_GEMMA4.bat" -ForegroundColor Red
    exit 1
}

$isWin = ($IsWindows -or $env:OS -match "Windows")
if ($isWin) {
    Write-Host "[vLLM] Windows：经 WSL Ubuntu 启动（原生 vLLM 不支持 Windows）…" -ForegroundColor Yellow
    wsl -d Ubuntu -- bash -lc "pkill -f 'vllm.entrypoints.openai.api_server' 2>/dev/null || true"
    Start-Sleep -Seconds 2
    wsl -d Ubuntu -- bash -lc "sed -i 's/\r$//' '$wslScript' 2>/dev/null || true; chmod +x '$wslScript'"
    $wslOut = Join-Path $logDir "vllm-wsl.log"
    Start-Process -FilePath "wsl.exe" -ArgumentList @(
        "-d", "Ubuntu",
        "-e", "bash", "-lc",
        "exec bash '$wslScript' >> '$wslLog' 2>&1"
    ) -WindowStyle Hidden | Out-Null
    Write-Host "[vLLM] WSL 日志: wsl -d Ubuntu -- tail -f $wslLog" -ForegroundColor DarkGray
    Write-Host "[vLLM] 镜像日志: $wslOut" -ForegroundColor DarkGray
} else {
    $py = (Get-Command python3 -ErrorAction SilentlyContinue).Source
    if (-not $py) { $py = "python3" }
    Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Process -FilePath $py -ArgumentList @(
        "-m", "vllm.entrypoints.openai.api_server",
        "--model", "D:\models\Gemma-4-26B-A4B-NVFP4",
        "--host", "127.0.0.1", "--port", "$Port",
        "--max-model-len", "32768", "--gpu-memory-utilization", "0.90"
    ) -RedirectStandardOutput (Join-Path $logDir "vllm-serve.log") `
      -RedirectStandardError (Join-Path $logDir "vllm-serve.err.log") -WindowStyle Hidden | Out-Null
}

$deadline = (Get-Date).AddSeconds($WaitSec)
$n = 0
while ((Get-Date) -lt $deadline) {
    if (Test-VllmUp) {
        try {
            $m = Invoke-RestMethod "http://127.0.0.1:$Port/v1/models" -TimeoutSec 15
            $id = $m.data[0].id
            Write-Host "[vLLM] 就绪 model=$id" -ForegroundColor Green
        } catch {
            Write-Host "[vLLM] 就绪 (health OK)" -ForegroundColor Green
        }
        exit 0
    }
    $n++
    if ($n % 20 -eq 0) {
        Write-Host "[vLLM] 等待加载… ${n}x5s"
        if ($isWin) {
            wsl -d Ubuntu -- bash -lc "tail -3 '$wslLog' 2>/dev/null || true"
        }
    }
    Start-Sleep -Seconds 5
}

Write-Host "[vLLM] 超时 (${WaitSec}s)。查看 WSL 日志: wsl tail $wslLog" -ForegroundColor Red
exit 1
