# 杀进程并重启 ONYX-OVERRIDE（本机桌面项目）
# 1) 释放 8000（FastAPI / uvicorn）
# 2) 结束由本项目启动的 Electron（匹配命令行，不误杀其它 Electron 应用）
# 3) 启动 START_APP.bat（会再起 Electron + 后端）
$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path $PSScriptRoot -Parent

Write-Host '=== 结束占用 8000 的进程 ===' -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object {
        if ($_ -and $_ -gt 0) {
            Write-Host "  Stop-Process Id=$_"
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    }
Start-Sleep -Seconds 1

Write-Host '=== 结束本项目 Electron（命令行含 ai-agent-project）===' -ForegroundColor Cyan
Get-CimInstance Win32_Process -Filter "Name='electron.exe'" |
    Where-Object {
        $_.CommandLine -and (
            $_.CommandLine -match 'ai-agent-project' -or
            $_.CommandLine -match 'onyx-override-desktop' -or
            $_.CommandLine -match 'ONYX-OVERRIDE'
        )
    } |
    ForEach-Object {
        Write-Host "  Stop-Process Id=$($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
Start-Sleep -Seconds 1

$bat = Join-Path $root 'START_APP.bat'
if (-not (Test-Path $bat)) {
    Write-Host "未找到: $bat" -ForegroundColor Red
    exit 1
}

Write-Host '=== 启动 START_APP.bat ===' -ForegroundColor Cyan
Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', "`"$bat`"") -WorkingDirectory $root -WindowStyle Normal
Write-Host '已在新窗口启动。请等待界面出现；后端约数秒内监听 http://127.0.0.1:8000' -ForegroundColor Green
