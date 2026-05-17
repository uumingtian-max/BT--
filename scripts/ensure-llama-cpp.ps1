# 确保本地 llama.cpp OpenAI 兼容网关已就绪（由 launcher\START_APP.bat 调用）
param(
    [int]$WaitSec = 600
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envFile = Join-Path $root "backend\.env"
$logDir = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Read-EnvFile([string]$Path) {
    $map = @{}
    if (-not (Test-Path $Path)) { return $map }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $s = [string]$line
        if (-not $s) { continue }
        $trim = $s.Trim()
        if (-not $trim -or $trim.StartsWith("#")) { continue }
        if ($trim.StartsWith("export ")) { $trim = $trim.Substring(7).Trim() }
        $eq = $trim.IndexOf("=")
        if ($eq -le 0) { continue }
        $key = $trim.Substring(0, $eq).Trim()
        $value = $trim.Substring($eq + 1).Trim()
        if ($value.Length -ge 2) {
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
        }
        $map[$key] = $value
    }
    return $map
}

function Get-EnvValue($cfg, [string]$Key, [string]$Default = "") {
    if ($cfg.ContainsKey($Key) -and [string]::IsNullOrWhiteSpace([string]$cfg[$Key]) -eq $false) {
        return [string]$cfg[$Key]
    }
    return $Default
}

function Get-IntValue($cfg, [string]$Key, [int]$Default) {
    $raw = Get-EnvValue $cfg $Key ""
    if ([string]::IsNullOrWhiteSpace($raw)) { return $Default }
    $out = 0
    if ([int]::TryParse($raw, [ref]$out)) { return $out }
    return $Default
}

function Get-ModelIds($payload) {
    $ids = @()
    if ($null -eq $payload) { return $ids }
    foreach ($item in @($payload.data)) {
        if ($item -and $item.id) { $ids += [string]$item.id }
    }
    return $ids
}

function Test-LlamaGateway([string]$ModelsUrl) {
    try {
        $data = Invoke-RestMethod -Uri $ModelsUrl -UseBasicParsing -TimeoutSec 8
        return @{
            ok = $true
            ids = @(Get-ModelIds $data)
        }
    } catch {
        return @{
            ok = $false
            error = $_.Exception.Message
            ids = @()
        }
    }
}

function Get-PortOwnerInfo([int]$Port) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $conn) { return $null }
    $processId = [int]$conn.OwningProcess
    $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
    $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    return @{
        pid = $processId
        name = if ($proc) { $proc.ProcessName } else { "" }
        path = if ($cim) { [string]$cim.ExecutablePath } else { "" }
        commandLine = if ($cim) { [string]$cim.CommandLine } else { "" }
    }
}

function Stop-LlamaServerOnPort([int]$Port, [string]$ExpectedExe) {
    $owner = Get-PortOwnerInfo $Port
    if (-not $owner) { return $true }
    $exeNorm = ($ExpectedExe -replace '/', '\').ToLowerInvariant()
    $pathNorm = ([string]$owner.path -replace '/', '\').ToLowerInvariant()
    $cmdNorm = ([string]$owner.commandLine).ToLowerInvariant()
    $isLlama = $false
    if ($pathNorm -and $pathNorm -eq $exeNorm) { $isLlama = $true }
    elseif ($pathNorm -like "*\llama-server.exe") { $isLlama = $true }
    elseif ($cmdNorm -like "*llama-server.exe*") { $isLlama = $true }
    if (-not $isLlama) {
        Write-Host "[llama.cpp] 端口 $Port 已被其它进程占用：PID=$($owner.pid) Name=$($owner.name)" -ForegroundColor Yellow
        return $false
    }
    Write-Host "[llama.cpp] 清理旧的 llama-server 进程 PID=$($owner.pid)..." -ForegroundColor DarkYellow
    Stop-Process -Id $owner.pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    return $true
}

$cfg = Read-EnvFile $envFile

$baseUrl = (Get-EnvValue $cfg "OPENAI_BASE_URL" "http://127.0.0.1:8001/v1").TrimEnd("/")
$baseUri = [Uri]$baseUrl
$listenHost = if ($baseUri.Host) { $baseUri.Host } else { "127.0.0.1" }
$port = if ($baseUri.Port -gt 0) { [int]$baseUri.Port } else { 8001 }
$modelsUrl = if ($baseUrl.EndsWith("/v1")) { "$baseUrl/models" } else { "$baseUrl/v1/models" }
$expectedModel = Get-EnvValue $cfg "LOCKED_MODEL_ID" ""
if ([string]::IsNullOrWhiteSpace($expectedModel)) {
    $expectedModel = Get-EnvValue $cfg "AGENT_DEFAULT_MODEL" ""
}

$llamaExe = Get-EnvValue $cfg "LLAMA_CPP_EXE" ""
$modelPath = Get-EnvValue $cfg "LLAMA_CPP_MODEL" ""
$mmprojPath = Get-EnvValue $cfg "LLAMA_CPP_MMPROJ" ""
$alias = Get-EnvValue $cfg "LLAMA_CPP_ALIAS" ""
$apiKey = Get-EnvValue $cfg "OPENAI_API_KEY" "local"
$ctxSize = Get-IntValue $cfg "LLAMA_CPP_CTX_SIZE" 4096
$parallel = Get-IntValue $cfg "LLAMA_CPP_PARALLEL" 1
$batchSize = Get-IntValue $cfg "LLAMA_CPP_BATCH_SIZE" 512
$ubatchSize = Get-IntValue $cfg "LLAMA_CPP_UBATCH_SIZE" 256
$fitTarget = Get-IntValue $cfg "LLAMA_CPP_FIT_TARGET" 1536
$gpuLayers = Get-EnvValue $cfg "LLAMA_CPP_GPU_LAYERS" "auto"
$flashAttn = Get-EnvValue $cfg "LLAMA_CPP_FLASH_ATTN" "on"

if ([string]::IsNullOrWhiteSpace($alias) -and -not [string]::IsNullOrWhiteSpace($expectedModel)) {
    $alias = $expectedModel
}
if ([string]::IsNullOrWhiteSpace($alias) -and -not [string]::IsNullOrWhiteSpace($modelPath)) {
    $alias = [System.IO.Path]::GetFileNameWithoutExtension($modelPath)
}
if ([string]::IsNullOrWhiteSpace($expectedModel)) {
    $expectedModel = $alias
}

$probe = Test-LlamaGateway $modelsUrl
if ($probe.ok -and (@($probe.ids) -contains $expectedModel -or @($probe.ids) -contains $alias -or -not $expectedModel)) {
    Write-Host "[llama.cpp] OpenAI 兼容网关已就绪：$($probe.ids -join ', ')" -ForegroundColor Green
    exit 0
}

$canManageLocal = -not [string]::IsNullOrWhiteSpace($llamaExe)
if (-not $canManageLocal) {
    $why = if ($probe.ok) { "当前 8001 已有网关，但模型不匹配：$($probe.ids -join ', ')" } else { "未检测到可用网关" }
    Write-Host "[llama.cpp] $why，且 backend\.env 未配置 LLAMA_CPP_EXE，无法自动拉起本地 llama.cpp。" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path -LiteralPath $llamaExe)) {
    Write-Host "[llama.cpp] 未找到 LLAMA_CPP_EXE：$llamaExe" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath $modelPath)) {
    Write-Host "[llama.cpp] 未找到 LLAMA_CPP_MODEL：$modelPath" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath $mmprojPath)) {
    Write-Host "[llama.cpp] 未找到 LLAMA_CPP_MMPROJ：$mmprojPath" -ForegroundColor Red
    exit 1
}

if (-not (Stop-LlamaServerOnPort -Port $port -ExpectedExe $llamaExe)) {
    exit 1
}

$fileLog = Join-Path $logDir "llama-server.log"

Write-Host "[llama.cpp] 正在启动本地多模态 Gemma4 网关（model + mmproj）..." -ForegroundColor Cyan
Write-Host "[llama.cpp] model=$modelPath" -ForegroundColor DarkGray
Write-Host "[llama.cpp] mmproj=$mmprojPath" -ForegroundColor DarkGray
Write-Host "[llama.cpp] alias=$alias port=$port ctx=$ctxSize gpu_layers=$gpuLayers" -ForegroundColor DarkGray

$serverArgs = @(
    "--host", $listenHost,
    "--port", "$port",
    "--model", $modelPath,
    "--mmproj", $mmprojPath,
    "--alias", $alias,
    "--ctx-size", "$ctxSize",
    "--parallel", "$parallel",
    "--batch-size", "$batchSize",
    "--ubatch-size", "$ubatchSize",
    "--gpu-layers", "$gpuLayers",
    "--flash-attn", "$flashAttn",
    "--fit", "on",
    "--fit-target", "$fitTarget",
    "--api-key", $apiKey,
    "--no-ui",
    "--log-file", $fileLog
)

$quotedArgs = $serverArgs | ForEach-Object {
    $arg = [string]$_
    if ($arg -match '[\s"]') {
        '"' + ($arg -replace '"', '\"') + '"'
    } else {
        $arg
    }
}

$launcherCmd = Join-Path $logDir "launch-llama-server.cmd"
$launcherLines = @(
    "@echo off",
    ('cd /d "{0}"' -f (Split-Path -Parent $llamaExe)),
    ('start "" /min "{0}" {1}' -f $llamaExe, ([string]::Join(' ', $quotedArgs)))
)
Set-Content -LiteralPath $launcherCmd -Value $launcherLines -Encoding Ascii

& cmd.exe /c $launcherCmd | Out-Null

$deadline = (Get-Date).AddSeconds($WaitSec)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    $probe = Test-LlamaGateway $modelsUrl
    if ($probe.ok -and (@($probe.ids) -contains $expectedModel -or @($probe.ids) -contains $alias -or -not $expectedModel)) {
        Write-Host "[llama.cpp] 网关就绪：$($probe.ids -join ', ')" -ForegroundColor Green
        exit 0
    }
}

Write-Host "[llama.cpp] 启动超时。请查看日志：$fileLog" -ForegroundColor Red
exit 1
