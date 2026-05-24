# Run AFTER closing Cursor/terminals using ai-agent-project (folder must not be locked).
$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$src = Join-Path $Desktop "ai-agent-project"
$dst = Join-Path $Desktop "Projects\BT-Blacklight"
if (-not (Test-Path $src)) {
    Write-Error "Source not found: $src"
}
if (Test-Path $dst) {
    Write-Error "Destination already exists: $dst"
}
New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
Move-Item -LiteralPath $src -Destination $dst
Write-Host "OK: $dst"
Write-Host "Reopen workspace: $dst\BT-Blacklight.code-workspace"
