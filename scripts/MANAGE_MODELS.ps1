# 黑光 Ollama 模型岗位管理（5090 24G 精简栈）
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ResidentModels = @(
    "nomic-embed-text:latest",
    "functiongemma:latest",
    "qwen3.5:9b",
    "deepseek-r1:7b",
    "deepseek-coder-v2:16b"
)
$OnDemandModels = @()
$PinModels = $ResidentModels
$RemovedModels = @(
    "qwen3.5:4b",
    "qwen3.5:0.8b",
    "nemotron-3-nano:4b",
    "granite4:3b",
    "qwen3:14b"
)

function Show-Menu {
    Write-Host "`n=== 黑光 Ollama 模型管理 ===" -ForegroundColor Cyan
    Write-Host "全常驻: 5模型一直挂VRAM (~20-22G) | 画图SD 语音F5"
    Write-Host "画图: generate_image / SD，不是 Ollama`n"
    Write-Host "[1] 拉取/更新 5 个全常驻模型 (ollama pull)"
    Write-Host "[2] 预热并 pin (keep_alive，需 backend/.env)"
    Write-Host "[3] 查看 ollama list / ollama ps"
    Write-Host "[4] 删除已裁重叠模型 ($($RemovedModels -join ', '))"
    Write-Host "[5] 显示 .env 岗位键说明"
    Write-Host "[0] 退出"
}

function Pull-PinModels {
    foreach ($m in $PinModels) {
        Write-Host "pull $m ..." -ForegroundColor Yellow
        ollama pull $m
    }
}

function Warm-PinModels {
    $Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    $py = & node (Join-Path $Root "scripts\resolve-python.cjs") 2>$null
    if (-not $py) { $py = "python" }
    & $py (Join-Path $Root "scripts\pin-ollama-models.ps1")
}

function Remove-OverlapModels {
    foreach ($m in $RemovedModels) {
        $exists = ollama list 2>$null | Select-String -Pattern "^$([regex]::Escape($m))\s"
        if ($exists) {
            Write-Host "rm $m" -ForegroundColor DarkYellow
            ollama rm $m
        }
    }
}

function Show-EnvRoles {
    @"
backend/.env 岗位键（勿重复定义 AGENT_DEFAULT_MODEL）:

  EMBED_MODEL          -> nomic-embed-text
  AGENT_ROUTER_MODEL   -> functiongemma
  AGENT_DEFAULT_MODEL  -> qwen3.5:9b   (主聊/视觉/tools)
  FAST_MODEL           -> qwen3.5:9b
  TASK_MODEL           -> qwen3.5:9b
  ORCH_VISION_MODEL    -> qwen3.5:9b
  REASONING_MODEL      -> deepseek-r1:7b
  ORCH_PLANNER_MODEL   -> deepseek-r1:7b
  CODE_MODEL           -> deepseek-coder-v2:16b  (常驻)
  BOSS_MODEL           -> deepseek-r1:7b (极限题，常驻)
  OLLAMA_RELEASE_ON_DEMAND=0  (不卸载，一直挂)
  CODE_SIMPLE_MODEL    -> qwen3.5:9b
  ORCH_CODER_MODEL     -> deepseek-coder-v2:16b
  一键重装: scripts\install-ollama-stack-2026.ps1

  LLM_BACKEND=ollama
  OLLAMA_KEEP_ALIVE=24h
  STRICT_MODEL_ROLES=1
"@ | Write-Host
}

do {
    Show-Menu
    $c = Read-Host "选择"
    switch ($c) {
        "1" { Pull-PinModels }
        "2" { Warm-PinModels }
        "3" { ollama list; ollama ps }
        "4" { Remove-OverlapModels }
        "5" { Show-EnvRoles }
        "0" { break }
        default { Write-Host "无效选项" -ForegroundColor Red }
    }
} while ($c -ne "0")
