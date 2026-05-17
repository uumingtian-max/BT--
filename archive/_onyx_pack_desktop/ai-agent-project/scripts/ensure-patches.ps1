# 补齐运行补丁：依赖、Playwright、品牌、.env 缺项、权重检查
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backend = Join-Path $root "backend"
$py = "$env:USERPROFILE\miniconda3\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

function Merge-EnvKeys($envFile, $exampleFiles) {
    if (-not (Test-Path $envFile)) {
        Copy-Item $exampleFiles[0] $envFile
    }
    $keys = @{}
    Get-Content $envFile -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') { $keys[$Matches[1]] = $true }
    }
    $added = 0
    foreach ($ex in $exampleFiles) {
        if (-not (Test-Path $ex)) { continue }
        foreach ($line in Get-Content $ex) {
            if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
                $k = $Matches[1]
                if (-not $keys.ContainsKey($k)) {
                    Add-Content -Path $envFile -Value $line
                    $keys[$k] = $true
                    $added++
                }
            }
        }
    }
    return $added
}

Write-Host "`n=== ONYX-OVERRIDE 补丁检查 ===" -ForegroundColor Cyan

Write-Host "[1/6] pip 依赖…" -ForegroundColor Yellow
& $py -m pip install -r (Join-Path $backend "requirements.txt") -q
& $py -m pip install -r (Join-Path $backend "requirements-extras.txt") -q

if (-not $env:PLAYWRIGHT_BROWSERS_PATH) {
    $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $env:LOCALAPPDATA "ms-playwright"
}
$chromium = Get-ChildItem -Path $env:PLAYWRIGHT_BROWSERS_PATH -Filter "chromium-*" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
Write-Host "[2/6] Playwright…" -ForegroundColor Yellow
if (-not $chromium) {
    & $py -m playwright install chromium
} else {
    Write-Host "  OK $($chromium.Name)" -ForegroundColor DarkGray
}

Write-Host "[3/6] 品牌图标…" -ForegroundColor Yellow
& $py (Join-Path $root "scripts\build-branding.py")

Write-Host "[4/6] 同步 .env 缺项…" -ForegroundColor Yellow
$envFile = Join-Path $backend ".env"
$examples = @(
    (Join-Path $backend ".env.example"),
    (Join-Path $backend ".env.local-gemma4.example")
)
$added = Merge-EnvKeys $envFile $examples
Write-Host "  追加 $added 项" -ForegroundColor DarkGray

Write-Host "[5/6] Gemma 权重…" -ForegroundColor Yellow
$w1 = "D:\models\Gemma-4-26B-A4B-NVFP4\model-00001-of-00002.safetensors"
$w2 = "D:\models\Gemma-4-26B-A4B-NVFP4\model-00002-of-00002.safetensors"
if ((Test-Path $w1) -and (Test-Path $w2)) {
    Write-Host "  OK 本地 Gemma 权重完整" -ForegroundColor Green
} else {
    Write-Host "  缺权重，可运行: scripts\install-gemma-weights.ps1" -ForegroundColor Yellow
}

Write-Host "[6/6] pytest…" -ForegroundColor Yellow
Push-Location $backend
& $py -m pytest tests -q --tb=line
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) { throw "pytest 失败 exit=$code" }

Write-Host "`n补丁就绪。`n" -ForegroundColor Green
