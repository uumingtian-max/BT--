# 确保 vLLM 在 8001 就绪；Windows 仅走 WSL Ubuntu + GPU
param(
    [int]$Port = 8001,
    [int]$WaitSec = 900,
    [switch]$Start,
    [switch]$ApplyEnv,
    [string]$ModelDir = "",
    [string]$WslModelDir = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envNano = Join-Path $root "backend\.env.local-vllm-nano.example"
$envFile = Join-Path $root "backend\.env"
$logDir = Join-Path $root "logs"

function Read-EnvMap([string]$Path) {
    $map = @{}
    if (-not (Test-Path $Path)) { return $map }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $t = ($line -replace '^\s*export\s+', '').Trim()
        if (-not $t -or $t.StartsWith("#")) { continue }
        $i = $t.IndexOf("=")
        if ($i -le 0) { continue }
        $map[$t.Substring(0, $i).Trim()] = $t.Substring($i + 1).Trim().Trim('"').Trim("'")
    }
    return $map
}

function ConvertTo-WslPath([string]$WinPath) {
    $p = $WinPath -replace '\\', '/'
    if ($p -match '^([A-Za-z]):(.*)$') { return "/mnt/$($Matches[1].ToLower())$($Matches[2])" }
    return $p
}

function Get-EnvValue($map, [string]$Key, [string]$Default = "") {
    if ($map.ContainsKey($Key) -and -not [string]::IsNullOrWhiteSpace([string]$map[$Key])) {
        return [string]$map[$Key]
    }
    return $Default
}

$cfg = Read-EnvMap $envFile
if (-not $ModelDir) {
    $ModelDir = Get-EnvValue $cfg "LOCAL_MODEL_DIR" "D:\models\Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4"
}
if (-not $WslModelDir) {
    $WslModelDir = Get-EnvValue $cfg "VLLM_WSL_MODEL_DIR" ""
    if (-not $WslModelDir) { $WslModelDir = ConvertTo-WslPath $ModelDir }
}

$wslScript = "$(ConvertTo-WslPath $root)/scripts/start-omni-vllm-wsl.sh"
$wslLog = "$(ConvertTo-WslPath $logDir)/vllm-wsl.log"
$wslMirror = Join-Path $logDir "vllm-wsl.log"
$wslLaunch = "$(ConvertTo-WslPath $logDir)/vllm-launch.sh"

function Test-VllmUp {
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 5
        return $r.StatusCode -eq 200
    } catch { return $false }
}

function Show-WslLogTail([int]$Lines = 8) {
    if (Test-Path -LiteralPath $wslMirror) {
        Get-Content -LiteralPath $wslMirror -Tail $Lines -ErrorAction SilentlyContinue |
            ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    }
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if ($ApplyEnv -and (Test-Path $envNano)) {
    Copy-Item -Force $envNano $envFile
    Write-Host "[vLLM] 已应用 backend\.env (Nemotron nano)" -ForegroundColor DarkGray
}

if (Test-VllmUp) {
    Write-Host "[vLLM] 已在 http://127.0.0.1:$Port 运行" -ForegroundColor Green
    try {
        & (Join-Path $root "scripts\sync-vllm-model-id.ps1") -BaseUrl "http://127.0.0.1:$Port/v1"
    } catch {
        Write-Host "[vLLM] sync model id skipped: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    exit 0
}

if (-not $Start) {
    Write-Host "[vLLM] 未运行。运行: powershell -File scripts\use-vllm.ps1" -ForegroundColor Red
    exit 1
}

if (-not ($IsWindows -or $env:OS -match "Windows")) {
    Write-Host "[vLLM] 非 Windows：请直接运行 vllm-serve-wsl.sh" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $ModelDir)) {
    Write-Host "[vLLM] 模型目录不存在: $ModelDir" -ForegroundColor Red
    exit 1
}

Write-Host "[vLLM] WSL Ubuntu + GPU（$WslModelDir）" -ForegroundColor Cyan

wsl -d Ubuntu -- true | Out-Null
$installCuda = ConvertTo-WslPath (Join-Path $root "scripts/install-wsl-cuda129.sh")
wsl -d Ubuntu -u root -e bash -c "sed -i 's/\r$//' '$installCuda' 2>/dev/null; bash '$installCuda' 2>/dev/null || true"
wsl -d Ubuntu -u root -e bash -c "ln -sf /home/rog/miniconda/bin/ninja /usr/bin/ninja 2>/dev/null || true"

wsl -d Ubuntu -- bash -lc "pkill -f 'vllm.entrypoints.openai.api_server' 2>/dev/null || true"
Start-Sleep -Seconds 2

$modelEsc = $WslModelDir -replace "'", "'\''"
$rootEsc = (ConvertTo-WslPath $root) -replace "'", "'\''"
$launchBody = @"
#!/usr/bin/env bash
set -euo pipefail
export CUDA_HOME=/usr/local/cuda-12.9
export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13 CUDAHOSTCXX=/usr/bin/g++-13
export PATH="/usr/local/cuda-12.9/bin:/home/rog/miniconda/bin:/usr/bin:${PATH:-}"
export MODEL_DIR='$modelEsc'
export PORT=$Port
export VLLM_LOG='$wslLog'
export VLLM_GPU_UTIL=0.78
export VLLM_MAX_MODEL_LEN=4096
export VLLM_MAX_NUM_SEQS=2
rm -rf "`$HOME/.cache/flashinfer" 2>/dev/null || true
find '$rootEsc/scripts' -maxdepth 1 -name '*.sh' -exec sed -i 's/\r$//' {} + 2>/dev/null || true
chmod +x '$wslScript'
: > "`$VLLM_LOG"
if command -v setsid >/dev/null 2>&1; then
  setsid bash '$wslScript' >> "`$VLLM_LOG" 2>&1 &
else
  nohup bash '$wslScript' >> "`$VLLM_LOG" 2>&1 &
fi
echo "started pid=$!"
"@
$launchWin = Join-Path $logDir "vllm-launch.sh"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($launchWin, ($launchBody -replace "`r`n", "`n"), $utf8NoBom)
$launchOut = wsl -d Ubuntu -- bash -lc "sed -i 's/\r$//' '$wslLaunch' && chmod +x '$wslLaunch' && bash '$wslLaunch'"
Write-Host "[vLLM] $launchOut" -ForegroundColor DarkGray
Write-Host "[vLLM] 已在 WSL 后台启动（start-omni-vllm-wsl.sh）" -ForegroundColor DarkGray
Write-Host "[vLLM] 日志: tail -f $wslMirror" -ForegroundColor DarkGray

$deadline = (Get-Date).AddSeconds($WaitSec)
$n = 0
while ((Get-Date) -lt $deadline) {
    if (Test-VllmUp) {
        try {
            $m = Invoke-RestMethod "http://127.0.0.1:$Port/v1/models" -TimeoutSec 30
            $id = $m.data[0].id
            Write-Host "[vLLM] 就绪 model=$id" -ForegroundColor Green
            & (Join-Path $root "scripts\sync-vllm-model-id.ps1") -BaseUrl "http://127.0.0.1:$Port/v1"
        } catch {
            Write-Host "[vLLM] 就绪 (health OK)" -ForegroundColor Green
        }
        exit 0
    }
    $n++
    if ($n % 6 -eq 0) {
        Write-Host "[vLLM] 加载中… $([int]($n * 5))s（Nemotron 首次约 5–15 分钟）"
        Show-WslLogTail 6
    }
    Start-Sleep -Seconds 5
}

Write-Host "[vLLM] 超时。最近日志:" -ForegroundColor Red
Get-Content -LiteralPath $wslMirror -Tail 50 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
exit 1
