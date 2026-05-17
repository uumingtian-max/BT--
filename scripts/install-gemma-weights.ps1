# 将 Downloads 里两个 safetensors 放入 D:\models\Gemma-4-26B-A4B-NVFP4
param(
    [string]$SourceDir = "$env:USERPROFILE\Documents\Downloads",
    [string]$TargetDir = "D:\models\Gemma-4-26B-A4B-NVFP4",
    [switch]$Move
)

$ErrorActionPreference = "Stop"
$files = @("model-00001-of-00002.safetensors", "model-00002-of-00002.safetensors")

if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
}

foreach ($name in $files) {
    $src = Join-Path $SourceDir $name
    $dst = Join-Path $TargetDir $name
    if (-not (Test-Path $src)) {
        throw "找不到源文件: $src"
    }
    if ((Test-Path $dst) -and ((Get-Item $dst).Length -eq (Get-Item $src).Length)) {
        Write-Host "已存在且大小一致，跳过: $name" -ForegroundColor DarkGray
        continue
    }
    $gb = [math]::Round((Get-Item $src).Length / 1GB, 2)
    Write-Host "复制 $name ($gb GB) -> $TargetDir …" -ForegroundColor Cyan
    if ($Move) {
        Move-Item -LiteralPath $src -Destination $dst -Force
    } else {
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
    $s = Get-Item $src -ErrorAction SilentlyContinue
    $d = Get-Item $dst
    if ($s -and $d.Length -ne $s.Length) { throw "复制后大小不一致: $name" }
    Write-Host "  完成: $name" -ForegroundColor Green
}

$idx = Join-Path $TargetDir "model.safetensors.index.json"
if (-not (Test-Path $idx)) { throw "缺少 model.safetensors.index.json" }
foreach ($name in $files) {
    if (-not (Test-Path (Join-Path $TargetDir $name))) { throw "缺少 $name" }
}
Write-Host "`n模型目录已完整，可启动 vLLM。" -ForegroundColor Green
Write-Host "下一步: powershell -File scripts\setup-local-gemma4-vllm.ps1 -Start -ApplyEnv"
