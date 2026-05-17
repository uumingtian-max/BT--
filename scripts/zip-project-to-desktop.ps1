# Packs the repo into a ZIP on the Desktop. Excludes bulky / machine-local paths.
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$folderName = Split-Path $projectRoot -Leaf
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$zipPath = Join-Path ([Environment]::GetFolderPath('Desktop')) "$folderName-$stamp.zip"

$excludePatterns = @(
  '[\\/]node_modules[\\/]'
  '[\\/]\.git[\\/]'
  '[\\/]__pycache__[\\/]'
  '[\\/]\.pytest_cache[\\/]'
  '[\\/]\.venv[\\/]'
  '[\\/]venv[\\/]'
  '[\\/]\.cursor[\\/]'
  '[\\/]agent-transcripts[\\/]'
  '[\\/]mcps[\\/]'
  '[\\/]frontend[\\/]build[\\/]'
  '[\\/]dist[\\/]'
  '[\\/]\.next[\\/]'
)

function Test-ExcludedPath([string]$fullPath) {
  foreach ($p in $excludePatterns) {
    if ($fullPath -match $p) { return $true }
  }
  return $false
}

if (Test-Path -LiteralPath $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$zip = [System.IO.Compression.ZipFile]::Open(
  $zipPath,
  [System.IO.Compression.ZipArchiveMode]::Create
)

$files = @()
try {
  $files = @(Get-ChildItem -LiteralPath $projectRoot -Recurse -File -Force |
    Where-Object { -not (Test-ExcludedPath $_.FullName) })

  foreach ($f in $files) {
    $rel = $f.FullName.Substring($projectRoot.Length).TrimStart([char[]]@('\', '/'))
    $entryName = ($folderName + '/' + ($rel -replace '\\', '/'))
    $entry = $zip.CreateEntry($entryName)
    $entryStream = $entry.Open()
    try {
      $fileStream = [System.IO.File]::OpenRead($f.FullName)
      try {
        $fileStream.CopyTo($entryStream)
      }
      finally {
        $fileStream.Dispose()
      }
    }
    finally {
      $entryStream.Dispose()
    }
  }
}
finally {
  $zip.Dispose()
}

Write-Host "ZIP written: $zipPath"
Write-Host "Files added: $($files.Count)"
