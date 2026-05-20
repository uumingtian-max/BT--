$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Backend = Join-Path $Root "backend"
$Logs = Join-Path $Root "logs"
$resolve = Join-Path $Root "scripts\resolve-python.cjs"
$Python = (& node $resolve 2>$null).Trim()
if (-not $Python) {
  $Python = Join-Path $env:USERPROFILE "miniconda3\envs\bt-heiguang\python.exe"
}
$ElectronCmd = Join-Path $Root "node_modules\.bin\electron.cmd"

New-Item -ItemType Directory -Force -Path $Logs | Out-Null

function Stop-OldAgentProcesses {
  try {
    Get-CimInstance Win32_Process -ErrorAction Stop |
      Where-Object {
        $_.CommandLine -and
        $_.Name -match "^(electron|node|python|pythonw)\.exe$" -and
        (
          $_.CommandLine -match [regex]::Escape($Root) -or
          ($_.CommandLine -match "uvicorn" -and $_.CommandLine -match "main:app" -and $_.CommandLine -match "--port 8000")
        ) -and
        $_.ProcessId -ne $PID
      } |
      ForEach-Object {
        try {
          Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } catch {}
      }
  } catch {
    Write-Host "[WARN] Skip old-process cleanup: $($_.Exception.Message)"
  }
}

function Test-Backend {
  try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
    return ($r.status -eq "ok")
  } catch {
    return $false
  }
}

function Test-BackendCurrent {
  if (-not (Test-Backend)) { return $false }
  try {
    $reg = Invoke-RestMethod -Uri "http://127.0.0.1:8000/meta/tools/registry" -TimeoutSec 3
    return ($reg.ok -eq $true)
  } catch {
    return $false
  }
}

function Stop-BackendPort8000 {
  Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
      try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }
}

function Wait-Backend {
  for ($i = 0; $i -lt 40; $i++) {
    if (Test-Backend) { return $true }
    Start-Sleep -Milliseconds 500
  }
  return $false
}

Set-Location $Root

if (-not (Test-Path $Python)) {
  Write-Host "[ERROR] Python not found: $Python"
  exit 1
}

if (-not (Test-Path $ElectronCmd)) {
  Write-Host "[ERROR] Electron not found: $ElectronCmd"
  Write-Host "Run npm install in $Root"
  exit 1
}

if (-not (Test-Path (Join-Path $Root "frontend\build\index.html"))) {
  Write-Host "[INFO] Frontend build missing, building..."
  Push-Location (Join-Path $Root "frontend")
  & (Join-Path $Root "scripts\npm.cjs") run build
  Pop-Location
}

Stop-OldAgentProcesses

if (-not (Test-BackendCurrent)) {
  if (Test-Backend) {
    Write-Host "[INFO] Stale backend on :8000 (missing /meta/tools/registry) — restarting..."
    Stop-BackendPort8000
    Start-Sleep -Seconds 2
  }
  Write-Host "[INFO] Starting backend..."
  $BackendOut = Join-Path $Logs "backend.out.log"
  $BackendErr = Join-Path $Logs "backend.err.log"
  $BackendCmd = "cd /d `"$Backend`" & `"$Python`" -m uvicorn main:app --host 127.0.0.1 --port 8000 1>> `"$BackendOut`" 2>> `"$BackendErr`""
  Start-Process -FilePath "cmd.exe" `
    -ArgumentList @("/c", $BackendCmd) `
    -WindowStyle Hidden
}

if (-not (Wait-Backend)) {
  Write-Host "[ERROR] Backend failed to start. See logs\backend.err.log"
  Get-Content -LiteralPath (Join-Path $Logs "backend.err.log") -Tail 40 -ErrorAction SilentlyContinue
  exit 1
}

Write-Host "[OK] Backend is healthy."
Write-Host "[INFO] Starting Electron..."
$ElectronCmdLine = "cd /d `"$Root`" & `"$ElectronCmd`" ."
Start-Process -FilePath "cmd.exe" `
  -ArgumentList @("/c", $ElectronCmdLine) `
  -WorkingDirectory $Root `
  -WindowStyle Normal
Write-Host "[OK] AI Agent launched."
