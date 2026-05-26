# 兼容入口 → scripts/sadtalker/run_portrait.ps1
& "$PSScriptRoot\sadtalker\run_portrait.ps1" @args
if ($LASTEXITCODE -ne $null) { exit $LASTEXITCODE }
