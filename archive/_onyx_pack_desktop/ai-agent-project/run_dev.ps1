# 开发模式启动：只监视当前目录，排除同级的 miniconda3，避免 pip 安装触发无限 reload。
Set-Location $PSScriptRoot
$py = Join-Path $env:USERPROFILE "miniconda3\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
& $py -m uvicorn main:app `
  --reload `
  --reload-dir $PSScriptRoot `
  --reload-exclude "miniconda3/**" `
  --reload-exclude "AppData/**" `
  --reload-exclude ".hf_cache/**" `
  --host 127.0.0.1 `
  --port 8000
