# Gemma 4 26B A4B NVFP4 本机 vLLM：下载（可选）+ 启动 + 写 ONYX .env
# 用法:
#   powershell -File scripts\setup-local-gemma4-vllm.ps1 -Download
#   powershell -File scripts\setup-local-gemma4-vllm.ps1 -Start
#   powershell -File scripts\setup-local-gemma4-vllm.ps1 -Download -Start -ApplyEnv

param(
    [string]$ModelId = "nvidia/Gemma-4-26B-A4B-NVFP4",
    [string]$ModelDir = "D:\models\Gemma-4-26B-A4B-NVFP4",
    [int]$Port = 8001,
    [switch]$Download,
    [switch]$Start,
    [switch]$ApplyEnv
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$EnvExample = Join-Path $Root "backend\.env.local-gemma4.example"
$EnvTarget = Join-Path $Root "backend\.env"

function Test-VllmUp {
    param([int]$P)
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$P/health" -UseBasicParsing -TimeoutSec 3
        return $r.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Get-Python {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }
    $c = "$env:USERPROFILE\miniconda3\python.exe"
    if (Test-Path $c) { return $c }
    throw "未找到 python，请先安装 Python 3.10+"
}

function Test-ModelWeightsComplete {
    param([string]$Dir)
    $required = @(
        "config.json",
        "model.safetensors.index.json",
        "model-00001-of-00002.safetensors",
        "model-00002-of-00002.safetensors"
    )
    foreach ($f in $required) {
        if (-not (Test-Path (Join-Path $Dir $f))) { return $false }
    }
    return $true
}

Write-Host "=== ONYX 本机 Gemma4 26B A4B NVFP4 + vLLM ===" -ForegroundColor Cyan
Write-Host "模型: $ModelId"
Write-Host "目录: $ModelDir"
Write-Host "端口: $Port (ONYX 用 OPENAI_BASE_URL=http://127.0.0.1:$Port/v1)"
Write-Host ""

$python = Get-Python

if ($Download) {
    Write-Host "[1/4] 检查 HF CLI ..." -ForegroundColor Yellow
    & $python -m pip install -q -U "huggingface_hub[cli]" 2>$null
    New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null
    $env:HF_ENDPOINT = "https://huggingface.co"
    $env:HUGGINGFACE_HUB_BASE_URL = "https://huggingface.co"
    Write-Host "[2/4] 下载模型（约 19GB+，需 HF 登录并接受许可）..." -ForegroundColor Yellow
    & hf download $ModelId --local-dir $ModelDir
    Write-Host "下载完成: $ModelDir" -ForegroundColor Green
} else {
    Write-Host "[跳过下载] 加 -Download 从 Hugging Face 拉取；或自行指定已下载目录 -ModelDir" -ForegroundColor DarkGray
}

if ($ApplyEnv -or -not (Test-Path $EnvTarget)) {
    Write-Host "[env] 写入 backend\.env（来自 .env.local-gemma4.example）" -ForegroundColor Yellow
    Copy-Item -Force $EnvExample $EnvTarget
    Write-Host "已应用本机配置: $EnvTarget" -ForegroundColor Green
}

if ($Start) {
    if (Test-VllmUp -P $Port) {
        Write-Host "vLLM 已在端口 $Port 运行。" -ForegroundColor Green
    } else {
        Write-Host "[3/4] 安装/检查 vLLM（首次较慢）..." -ForegroundColor Yellow
        & $python -m pip install -q -U vllm 2>$null
        $servePath = $ModelDir
        if (-not (Test-ModelWeightsComplete -Dir $ModelDir)) {
            if (Test-Path (Join-Path $ModelDir "config.json")) {
                Write-Host "[错误] 模型目录缺少权重分片。请先运行:" -ForegroundColor Red
                Write-Host "  powershell -File scripts\install-gemma-weights.ps1" -ForegroundColor Yellow
                exit 1
            }
            $servePath = $ModelId
            Write-Host "本地目录无完整权重，将让 vLLM 从 HF 拉取: $ModelId" -ForegroundColor DarkYellow
        } else {
            Write-Host "本地权重完整: $ModelDir" -ForegroundColor Green
        }
        Write-Host "[4/4] 启动 vLLM（新终端窗口）..." -ForegroundColor Yellow
        if ($IsWindows -or $env:OS -match "Windows") {
            Write-Host ""
            Write-Host "[错误] setup-local-gemma4-vllm -Start 无法在 Windows 上可靠拉起 GPU vLLM。" -ForegroundColor Red
            Write-Host "  【稳】Ollama: 安装 Ollama 后 copy backend\.env.example backend\.env，START_APP.bat" -ForegroundColor Yellow
            Write-Host "  【实验】WSL: scripts\ensure-vllm.ps1 -Start -ApplyEnv" -ForegroundColor Yellow
            Write-Host ""
            exit 1
        }
        $cmd = @"
cd /d `"$Root`"
`"$python`" -m vllm.entrypoints.openai.api_server --model `"$servePath`" --host 127.0.0.1 --port $Port --max-model-len 32768 --gpu-memory-utilization 0.90
"@
        Start-Process cmd -ArgumentList "/k", $cmd | Out-Null
        Write-Host "等待 vLLM 就绪 ..."
        $ok = $false
        for ($i = 0; $i -lt 120; $i++) {
            Start-Sleep -Seconds 2
            if (Test-VllmUp -P $Port) { $ok = $true; break }
        }
        if ($ok) {
            Write-Host "vLLM 已就绪: http://127.0.0.1:$Port/v1" -ForegroundColor Green
            try {
                $models = Invoke-RestMethod "http://127.0.0.1:$Port/v1/models" -TimeoutSec 10
                $first = $models.data[0].id
                if ($first) {
                    Write-Host "vLLM 模型 ID: $first" -ForegroundColor Cyan
                    if (Test-Path $EnvTarget) {
                        $lines = Get-Content $EnvTarget
                        $keys = @(
                            "AGENT_DEFAULT_MODEL", "ORCH_PLANNER_MODEL", "ORCH_CODER_MODEL",
                            "ORCH_REVIEWER_MODEL", "ORCH_VISION_MODEL", "ORCH_SPEECH_MODEL", "AGENT_EVOLVE_MODEL"
                        )
                        $out = foreach ($line in $lines) {
                            $hit = $false
                            foreach ($k in $keys) {
                                if ($line -match "^\s*$k\s*=") {
                                    "$k=$first"
                                    $hit = $true
                                    break
                                }
                            }
                            if (-not $hit) { $line }
                        }
                        Set-Content -Path $EnvTarget -Value $out -Encoding UTF8
                        Write-Host "已写入 backend\.env 模型 ID" -ForegroundColor Green
                    }
                }
            } catch {
                Write-Host "未能自动读取 /v1/models，请手动核对 AGENT_DEFAULT_MODEL" -ForegroundColor Yellow
            }
        } else {
            Write-Host "vLLM 启动超时，请查看新开的 cmd 窗口报错。" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "下一步:" -ForegroundColor Cyan
Write-Host "  1) 若未 -ApplyEnv: copy backend\.env.local-gemma4.example backend\.env"
Write-Host "  2) 运行 START_APP_LOCAL.bat 或 START_APP.bat"
Write-Host "  3) /meta/doctor 应显示 openai_compatible；聊天选 nvidia/Gemma-4-26B-A4B-NVFP4"
