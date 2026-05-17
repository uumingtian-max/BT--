param(
    [string]$BaseUrl = "https://api.openai.com/v1",
    [string]$Model = "",
    [string]$ApiKey = "",
    [switch]$NoPrompt,
    [switch]$SkipProbe
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$EnvTarget = Join-Path $Root "backend\.env"

function Read-Value {
    param(
        [string]$Prompt,
        [string]$Default = "",
        [switch]$Secret
    )
    if ($NoPrompt) { return $Default }
    $suffix = if ($Default) { " [$Default]" } else { "" }
    if ($Secret) {
        $secure = Read-Host "$Prompt$suffix" -AsSecureString
        if ($secure.Length -eq 0) { return $Default }
        $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
    }
    $value = Read-Host "$Prompt$suffix"
    if ([string]::IsNullOrWhiteSpace($value)) { return $Default }
    return $value.Trim()
}

function Set-EnvLine {
    param(
        [string[]]$Lines,
        [string]$Key,
        [string]$Value
    )
    $escaped = [regex]::Escape($Key)
    $found = $false
    $out = foreach ($line in $Lines) {
        if ($line -match "^\s*#?\s*$escaped\s*=") {
            $found = $true
            "$Key=$Value"
        } else {
            $line
        }
    }
    if (-not $found) { $out += "$Key=$Value" }
    return $out
}

if (-not (Test-Path $EnvTarget)) {
    $example = Join-Path $Root "backend\.env.example"
    if (Test-Path $example) {
        Copy-Item -Force $example $EnvTarget
    } else {
        New-Item -ItemType File -Force -Path $EnvTarget | Out-Null
    }
}

$existing = Get-Content -LiteralPath $EnvTarget -ErrorAction SilentlyContinue
$existingDefaultModel = ($existing | Where-Object { $_ -match '^\s*AGENT_DEFAULT_MODEL\s*=\s*(.+)\s*$' } | Select-Object -First 1)
$existingModel = if ($existingDefaultModel) { ($existingDefaultModel -replace '^\s*AGENT_DEFAULT_MODEL\s*=\s*', '').Trim() } else { "" }

if (-not $ApiKey) { $ApiKey = $env:OPENAI_API_KEY }
if (-not $Model) {
    $defaultModel = if ($existingModel -and $existingModel -notmatch 'Gemma|/mnt/d/models|qwen3') { $existingModel } else { "gpt-4.1" }
    $Model = Read-Value -Prompt "OpenAI model id" -Default $defaultModel
}
if (-not $ApiKey) { $ApiKey = Read-Value -Prompt "OpenAI API key" -Secret }
if (-not $ApiKey) { throw "OPENAI_API_KEY is required." }

$BaseUrl = Read-Value -Prompt "OpenAI-compatible base URL" -Default $BaseUrl
$BaseUrl = $BaseUrl.TrimEnd("/")
$Model = $Model.Trim()

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = "$EnvTarget.backup-$stamp"
Copy-Item -Force $EnvTarget $backup

$lines = Get-Content -LiteralPath $EnvTarget
$settings = [ordered]@{
    "LOCK_SINGLE_MODEL" = "1"
    "LOCKED_MODEL_ID" = $Model
    "LLM_BACKEND" = "openai_compatible"
    "OPENAI_BASE_URL" = $BaseUrl
    "OPENAI_API_KEY" = $ApiKey
    "AGENT_DEFAULT_MODEL" = $Model
    "ORCH_PLANNER_MODEL" = $Model
    "ORCH_CODER_MODEL" = $Model
    "ORCH_REVIEWER_MODEL" = $Model
    "ORCH_VISION_MODEL" = $Model
    "ORCH_SPEECH_MODEL" = $Model
    "AGENT_EVOLVE_MODEL" = $Model
    "TASK_DECOMPOSE_BACKEND" = "openai_compatible"
    "EXTRA_MODEL_IDS" = $Model
    "AGENT_EVOLVE_LLM" = "0"
    "HABIT_EVOLVE_ON_CHECK" = "0"
}

foreach ($k in $settings.Keys) {
    $lines = Set-EnvLine -Lines $lines -Key $k -Value $settings[$k]
}
Set-Content -LiteralPath $EnvTarget -Value $lines -Encoding UTF8

Write-Host ""
Write-Host "已切换 ONYX 到 OpenAI-compatible provider。" -ForegroundColor Green
Write-Host "配置文件: $EnvTarget"
Write-Host "备份文件: $backup"
Write-Host "模型: $Model"
Write-Host "Base URL: $BaseUrl"

if (-not $SkipProbe) {
    try {
        $headers = @{ Authorization = "Bearer $ApiKey" }
        $models = Invoke-RestMethod -Uri "$BaseUrl/models" -Headers $headers -TimeoutSec 20
        $count = @($models.data).Count
        Write-Host "连通性: OK，/models 返回 $count 个模型。" -ForegroundColor Green
    } catch {
        Write-Host "连通性: 未通过。配置已写入，稍后启动 ONYX 仍可在系统面板重新检测。" -ForegroundColor Yellow
        Write-Host $_.Exception.Message -ForegroundColor DarkYellow
    }
}

Write-Host ""
Write-Host "下一步: 关闭已打开的 ONYX，然后双击 ONYX-OVERRIDE.lnk 或运行 START_APP.bat。"
