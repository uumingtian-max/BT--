$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envFile = Join-Path $root "backend\.env"

if (!(Test-Path $envFile)) {
  New-Item -ItemType File -Path $envFile -Force | Out-Null
}

$bytes = New-Object byte[] 24
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$token = [Convert]::ToBase64String($bytes).Replace("+", "").Replace("/", "").Replace("=", "")

$raw = Get-Content -LiteralPath $envFile -Raw -Encoding UTF8
if ($raw -match "(?m)^MOBILE_ACCESS_TOKEN=.*$") {
  $raw = $raw -replace "(?m)^MOBILE_ACCESS_TOKEN=.*$", "MOBILE_ACCESS_TOKEN=$token"
} else {
  $raw = $raw.TrimEnd() + "`r`nMOBILE_ACCESS_TOKEN=$token`r`n"
}
Set-Content -LiteralPath $envFile -Encoding UTF8 -Value $raw

Write-Host ""
Write-Host "[ONYX] Remote mobile token is ready:"
Write-Host "  $token"
Write-Host ""
Write-Host "[ONYX] Keep START_MOBILE.bat running on the computer."
Write-Host "[ONYX] For anywhere access, expose http://127.0.0.1:8002 (or your BACKEND_PORT) with Cloudflare Tunnel or use Tailscale VPN."
Write-Host "[ONYX] Public-domain mobile access will ask for this token once."
