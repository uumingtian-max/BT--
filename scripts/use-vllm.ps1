# 一键：合并 Nano-Omni .env 并启动 WSL vLLM（文档入口）
param(
    [switch]$SkipStart,
    [string]$ModelDir = "",
    [int]$WaitSec = 900
)

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ensure = Join-Path $root "scripts\ensure-vllm.ps1"
$args = @("-ApplyEnv", "-WaitSec", $WaitSec)
if ($ModelDir) { $args += @("-ModelDir", $ModelDir) }
if (-not $SkipStart) { $args += "-Start" }
& powershell -NoProfile -ExecutionPolicy Bypass -File $ensure @args
