<#
BKLT 黑光 / BLACKLIGHT - NVIDIA Agent Stack Downloader

默认下载目录：D:\models
用途：一次性下载黑光推荐的 NVIDIA/NVlabs 模型栈。

推荐先运行：
  powershell -ExecutionPolicy Bypass -File .\scripts\download-nvidia-agent-stack.ps1

如果 Hugging Face 要求登录：
  huggingface-cli login
然后再运行本脚本。
#>

param(
  [string]$ModelRoot = "D:\models",
  [ValidateSet("8B", "14B")]
  [string]$TerminalSize = "14B",
  [switch]$SkipVideo,
  [switch]$SkipOCR,
  [switch]$SkipSafety
)

$ErrorActionPreference = "Stop"

function Write-Step($Text) {
  Write-Host "`n[BKLT] $Text" -ForegroundColor Cyan
}

function Ensure-Command($Name, $InstallHint) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "找不到命令：$Name。$InstallHint"
  }
}

function Download-HFRepo($RepoId, $LocalName) {
  $Target = Join-Path $ModelRoot $LocalName
  Write-Step "Downloading $RepoId -> $Target"
  New-Item -ItemType Directory -Force -Path $Target | Out-Null
  huggingface-cli download $RepoId --local-dir $Target --resume-download
}

Write-Step "Checking Python / pip / huggingface-cli"
Ensure-Command python "请先安装 Python 3.10+，并勾选 Add Python to PATH。"
python -m pip install -U huggingface_hub hf_xet

if (-not (Get-Command huggingface-cli -ErrorAction SilentlyContinue)) {
  $userScripts = Join-Path $env:APPDATA "Python\Python312\Scripts"
  if (Test-Path $userScripts) { $env:Path += ";$userScripts" }
}
Ensure-Command huggingface-cli "请执行：python -m pip install -U huggingface_hub hf_xet，然后重新打开 PowerShell。"

New-Item -ItemType Directory -Force -Path $ModelRoot | Out-Null

# 1) 主脑：BKLT 黑光主 Agent / reasoning + chat + tool use
Download-HFRepo "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4" "NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4"

# 2) 终端模型：shell / PowerShell / code-agent
if ($TerminalSize -eq "8B") {
  Download-HFRepo "nvidia/Nemotron-Terminal-8B" "Nemotron-Terminal-8B"
} else {
  Download-HFRepo "nvidia/Nemotron-Terminal-14B" "Nemotron-Terminal-14B"
}

# 3) 记忆 / RAG：embedding + rerank
Download-HFRepo "nvidia/llama-nemotron-embed-1b-v2" "llama-nemotron-embed-1b-v2"
Download-HFRepo "nvidia/llama-nemotron-rerank-1b-v2" "llama-nemotron-rerank-1b-v2"

# 4) 视频：LongLive 快速 NVFP4 S2
if (-not $SkipVideo) {
  Download-HFRepo "Efficient-Large-Model/LongLive-2.0-5B-NVFP4-S2" "LongLive-2.0-5B-NVFP4-S2"
}

# 5) OCR：截图 / PDF / 文档图像识别
if (-not $SkipOCR) {
  Download-HFRepo "nvidia/nemotron-ocr-v2" "nemotron-ocr-v2"
}

# 6) 安全：Agent 执行前安全审查
if (-not $SkipSafety) {
  Download-HFRepo "nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3" "Llama-3.1-Nemotron-Safety-Guard-8B-v3"
}

Write-Step "Done. Models are under $ModelRoot"
Write-Host "`n下一步：先把主脑接到 vLLM / OpenAI-compatible 网关，再让 BKLT 黑光指向该模型 ID。" -ForegroundColor Green
