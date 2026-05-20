# 关闭 conda/pytest 误报
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $here "apply-cursor-ide-fix.ps1")
