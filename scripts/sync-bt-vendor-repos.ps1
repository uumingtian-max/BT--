# Sync curated vendor repos for BT (reference only). Run from repo root.
param(
    [switch]$All,
    [switch]$ConfirmNetworkSync
)

if (-not $ConfirmNetworkSync) {
    Write-Host "BLOCKED: this script clones/pulls external vendor repositories." -ForegroundColor Red
    Write-Host "Run only after explicit user approval: .\scripts\sync-bt-vendor-repos.ps1 -ConfirmNetworkSync" -ForegroundColor Yellow
    exit 2
}

$root = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $root "vendor\repos.manifest.json"
if (-not (Test-Path $manifestPath)) {
    throw "Missing $manifestPath"
}

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

function Write-GitLines {
    param([object]$Lines)
    foreach ($line in @($Lines)) {
        if ($null -ne $line) { Write-Host $line }
    }
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$GitArgs
    )
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $out = & git @GitArgs 2>&1
        Write-GitLines $out
        if ($LASTEXITCODE -ne 0) {
            throw "git exit ${LASTEXITCODE}: git $($GitArgs -join ' ')"
        }
    }
    finally {
        $ErrorActionPreference = $prevEap
    }
}

function Sync-Repo {
    param($repo)
    $dest = Join-Path $root ($repo.path -replace '/', '\')
    $parent = Split-Path $dest -Parent
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    if (Test-Path (Join-Path $dest ".git")) {
        Write-Host ">>> pull $($repo.id)"
        Invoke-Git -GitArgs @("-C", $dest, "pull", "--ff-only")
        $rev = (& git -C $dest rev-parse --short HEAD 2>$null)
        if ($rev) { Write-Host "    at $rev" }
    }
    else {
        Write-Host ">>> clone $($repo.id) -> $($repo.path)"
        if ($repo.shallow) {
            Invoke-Git -GitArgs @("clone", "--depth", "1", $repo.url, $dest)
        }
        else {
            Invoke-Git -GitArgs @("clone", $repo.url, $dest)
        }
    }
}

$synced = @()
foreach ($repo in $manifest.repos) {
    $want = $repo.clone_default -eq $true
    if ($All) { $want = $true }
    if (-not $want) { continue }
    Sync-Repo $repo
    $synced += $repo.id
}

if ($synced.Count -eq 0) {
    Write-Host "Nothing to sync (use -All for optional repos)."
}
else {
    Write-Host "Synced: $($synced -join ', ')"
}
Write-Host "Done. BT runtime uses backend/agent_skills, not vendor/."
