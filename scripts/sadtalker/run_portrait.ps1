# SadTalker 测试：用你的 portrait + 中文示例音频
# 可在 base 下直接跑；会自动用 conda 环境 sadtalker
# 用法: cd ai-agent-project; .\scripts\sadtalker\run_portrait.ps1

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
$SadEnv = "sadtalker"

function Get-PythonInvoker {
    if ($env:CONDA_DEFAULT_ENV -eq $SadEnv) {
        return @{ Mode = "active"; Python = "python" }
    }
    $conda = Get-Command conda -ErrorAction SilentlyContinue
    if (-not $conda) {
        Write-Host "当前是 $($env:CONDA_DEFAULT_ENV)，不是 $SadEnv，且找不到 conda。" -ForegroundColor Red
        Write-Host "请先运行: conda activate $SadEnv" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "当前环境: $($env:CONDA_DEFAULT_ENV) -> 使用 conda run -n $SadEnv" -ForegroundColor Yellow
    return @{ Mode = "conda-run"; Python = "conda run -n $SadEnv --no-capture-output python" }
}

$py = Get-PythonInvoker

$Portrait = "$Root\frontend\public\digital-human\photo.png"
if (-not (Test-Path $Portrait)) { $Portrait = "$Root\face.png" }
if (-not (Test-Path $Portrait)) {
    Write-Host "找不到人像: 请放 face.png 或 frontend\public\digital-human\photo.png" -ForegroundColor Red
    exit 1
}

Write-Host "修复 sadtalker 环境 (basicsr + librosa/pkg_resources)..." -ForegroundColor Cyan
if ($py.Mode -eq "active") {
    & python "$Root\scripts\sadtalker\fix_env.py"
} else {
    & conda run -n $SadEnv --no-capture-output python "$Root\scripts\sadtalker\fix_env.py"
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Set-Location "$Root\SadTalker"
$out = "$Root\SadTalker\results"
New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host "推理: $Portrait" -ForegroundColor Cyan
$inferArgs = @(
    "inference.py",
    "--driven_audio", "examples/driven_audio/bus_chinese.wav",
    "--source_image", $Portrait,
    "--result_dir", $out,
    "--still",
    "--preprocess", "crop"
)

if ($py.Mode -eq "active") {
    & python @inferArgs
} else {
    & conda run -n $SadEnv --no-capture-output python @inferArgs
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "完成。查看: $out" -ForegroundColor Green
    Get-ChildItem $out -Recurse -Filter *.mp4 | Sort-Object LastWriteTime -Descending | Select-Object -First 3 FullName
} else {
    exit $LASTEXITCODE
}
