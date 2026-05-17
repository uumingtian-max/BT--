#Requires -Version 5.1
<#
.SYNOPSIS
  Start NVIDIA NIM: Meta Llama 4 Maverick 17B 128E Instruct (OpenAI-compatible /v1 on port 8000).

.DESCRIPTION
  Default image: nvcr.io/nim/meta/llama-4-maverick-17b-128e-instruct:latest
  Catalog: https://catalog.ngc.nvidia.com/orgs/nim/teams/meta/containers/llama-4-maverick-17b-128e-instruct

  Override image:  $env:NIM_IMAGE="nvcr.io/nim/meta/llama-3.1-8b-instruct:latest"; .\scripts\run-nim-llama-8b.ps1

  1) Set NGC_API_KEY (NGC Personal / Service key for nvcr.io).
  2) .\scripts\run-nim-llama-8b.ps1
  3) backend/.env: AGENT_DEFAULT_MODEL = id from curl http://127.0.0.1:8000/v1/models
#>
param(
  [string]$Image = "",
  [int]$Port = 8000
)

if (-not $Image) {
  $Image = ($env:NIM_IMAGE).Trim()
}
if (-not $Image) {
  $Image = "nvcr.io/nim/meta/llama-4-maverick-17b-128e-instruct:latest"
}

$ErrorActionPreference = "Stop"
if (-not $env:NGC_API_KEY) {
  Write-Error "请先设置环境变量 NGC_API_KEY（NGC 个人 API Key，需含 Catalog 权限）。"
  exit 1
}

$cache = Join-Path $env:USERPROFILE ".cache\nim"
New-Item -ItemType Directory -Force -Path $cache | Out-Null

Write-Host "Logging in to nvcr.io ..."
$env:NGC_API_KEY | docker login nvcr.io --username '$oauthtoken' --password-stdin

Write-Host "Starting NIM: $Image on port $Port ..."
docker run -it --rm --name nim-llama4-maverick `
  --gpus all `
  --shm-size=16GB `
  -e NGC_API_KEY=$($env:NGC_API_KEY) `
  -e NIM_RELAX_MEM_CONSTRAINTS=1 `
  -v "${cache}:/opt/nim/.cache" `
  -p "${Port}:8000" `
  $Image
