# 多轮实机锤炼：pytest x3 + API 探针 + 日志摘要
param(
    [int]$Rounds = 3,
    [switch]$SkipElectron
)

$ErrorActionPreference = "Continue"
$root = "c:\Users\ROG\Desktop\ai-agent-project"
$backend = Join-Path $root "backend"
$logDir = Join-Path $root "logs"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = Join-Path $logDir "hammer-$stamp.log"
$py = "$env:USERPROFILE\miniconda3\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
function Log($msg, $color = "Gray") {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Add-Content -Path $logFile -Value $line
    Write-Host $line -ForegroundColor $color
}

Log "========== ONYX-OVERRIDE 锤炼测试 ($Rounds 轮) ==========" "Cyan"
Log "日志: $logFile"

# 结束占用 8000 的旧进程（仅 uvicorn）
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2

$backendOut = Join-Path $logDir "backend-$stamp.log"
$backendErr = Join-Path $logDir "backend-$stamp.err.log"
$be = Start-Process -FilePath $py -ArgumentList @(
    "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"
) -WorkingDirectory $backend -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru -WindowStyle Hidden

Log "后端 PID=$($be.Id)" "Yellow"
$ready = $false
for ($i = 1; $i -le 45; $i++) {
    try {
        $h = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 2
        if ($h.status -eq "ok" -or $h.ok -eq $true -or $null -ne $h) { $ready = $true; break }
    } catch {
        try {
            $r = Invoke-WebRequest "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
    }
    Start-Sleep -Seconds 1
}
if (-not $ready) {
    Log "后端启动失败。stderr 末尾:" "Red"
    if (Test-Path $backendErr) { Get-Content $backendErr -Tail 30 | ForEach-Object { Log $_ "Red" } }
    Stop-Process -Id $be.Id -Force -ErrorAction SilentlyContinue
    exit 1
}
Log "后端 /health OK" "Green"

$endpoints = @(
    @{ Name = "health"; Url = "http://127.0.0.1:8000/health" },
    @{ Name = "meta/info"; Url = "http://127.0.0.1:8000/meta/info" },
    @{ Name = "meta/doctor"; Url = "http://127.0.0.1:8000/meta/doctor" },
    @{ Name = "agent/tools"; Url = "http://127.0.0.1:8000/agent/tools" },
    @{ Name = "scheduler/jobs"; Url = "http://127.0.0.1:8000/scheduler/jobs" },
    @{ Name = "gateway/status"; Url = "http://127.0.0.1:8000/gateway/status" },
    @{ Name = "mcp/tools"; Url = "http://127.0.0.1:8000/mcp/tools" }
)

$failures = @()
for ($round = 1; $round -le $Rounds; $round++) {
    Log "--- 第 $round / $Rounds 轮 pytest ---" "Cyan"
    Push-Location $backend
    $pytestLog = Join-Path $logDir "pytest-r$round-$stamp.log"
    & $py -m pytest tests -q --tb=short 2>&1 | Tee-Object -FilePath $pytestLog
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) {
        $failures += "pytest round $round exit $code"
        Log "pytest 第 $round 轮失败 (exit $code)" "Red"
    } else {
        Log "pytest 第 $round 轮通过" "Green"
    }

    Log "--- 第 $round 轮 API 探针 ---" "Cyan"
    foreach ($ep in $endpoints) {
        try {
            $r = Invoke-WebRequest $ep.Url -UseBasicParsing -TimeoutSec 8
            Log "  OK $($ep.Name) $($r.StatusCode)" "DarkGray"
        } catch {
            $msg = $_.Exception.Message
            Log "  FAIL $($ep.Name): $msg" "Red"
            $failures += "$($ep.Name): $msg"
        }
    }

    # 轻量 chat：按 backend\.env（Ollama 或 openai_compatible 网关）
    try {
        $chatModel = "qwen3.5:4b"
        $envPath = Join-Path $backend ".env"
        if (Test-Path $envPath) {
            Get-Content $envPath | ForEach-Object {
                if ($_ -match '^\s*AGENT_DEFAULT_MODEL\s*=\s*(.+)$') { $chatModel = $Matches[1].Trim() }
            }
        }
        $body = @{
            message    = "回复一个字：好"
            model      = $chatModel
            mode       = "chat"
            session_id = "hammer-test"
        } | ConvertTo-Json
        $chat = Invoke-WebRequest "http://127.0.0.1:8000/chat/" -Method POST `
            -ContentType "application/json" -Body $body -UseBasicParsing -TimeoutSec 300
        Log "  OK POST /chat/ $($chat.StatusCode)" "DarkGray"
    } catch {
        Log "  WARN POST /chat/: $($_.Exception.Message)" "Yellow"
    }
    Start-Sleep -Seconds 1
}

if (-not $SkipElectron) {
    Log "--- Electron 冒烟 ---" "Cyan"
    $env:NODE_ENV = "production"
    $el = Start-Process node -ArgumentList @(
        (Join-Path $root "scripts\npm.cjs"), "run", "electron"
    ) -WorkingDirectory $root -PassThru
    Start-Sleep -Seconds 6
    if ($el.HasExited) {
        $failures += "Electron exited early $($el.ExitCode)"
        Log "Electron 过早退出 $($el.ExitCode)" "Red"
    } else {
        Log "Electron 运行中，正常结束测试" "Green"
        Stop-Process -Id $el.Id -Force -ErrorAction SilentlyContinue
    }
    Get-Process -Name "electron" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

Log "--- 后端日志 (stderr 末 40 行) ---" "Yellow"
if (Test-Path $backendErr) {
    Get-Content $backendErr -Tail 40 -ErrorAction SilentlyContinue | ForEach-Object { Log "  $_" "DarkYellow" }
}
if (Test-Path $backendOut) {
    $outTail = Get-Content $backendOut -Tail 15 -ErrorAction SilentlyContinue
    if ($outTail) {
        Log "--- 后端 stdout 末 15 行 ---" "Yellow"
        $outTail | ForEach-Object { Log "  $_" "DarkGray" }
    }
}

Stop-Process -Id $be.Id -Force -ErrorAction SilentlyContinue

Log "========== 总结 ==========" "Cyan"
if ($failures.Count -eq 0) {
    Log "全部 $Rounds 轮通过，无硬错误。" "Green"
    exit 0
}
$failures | ForEach-Object { Log "FAIL: $_" "Red" }
Log "详见 $logFile" "Yellow"
exit 1
