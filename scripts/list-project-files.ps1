$ErrorActionPreference = 'SilentlyContinue'
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$outDir = Join-Path $root 'docs\archive'
$out = Join-Path $outDir 'PROJECT_FILE_INDEX.txt'
$skip = @('node_modules', '.git', '__pycache__', '.cursor', 'agent-transcripts', 'mcps', 'frontend\build', 'frontend/build')

function Test-SkipPath([string]$p) {
  foreach ($s in $skip) {
    if ($p -like "*\$s\*" -or $p -like "*/$s/*") { return $true }
  }
  return $false
}

if (-not (Test-Path $outDir)) {
  New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$lines = Get-ChildItem -LiteralPath $root -Recurse -File |
  Where-Object { -not (Test-SkipPath $_.FullName) } |
  ForEach-Object {
    $rel = $_.FullName.Substring($root.Path.Length).TrimStart('\')
    $rel -replace '\\', '/'
  } |
  Sort-Object

$header = @(
  "# AI Agent project file index",
  "# Root: $($root.Path)",
  "# Excluded path segments: $($skip -join ', ')",
  "# Total files listed: $($lines.Count)",
  "# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
  ""
)
($header + $lines) | Set-Content -LiteralPath $out -Encoding utf8
Write-Host "Wrote $out ($($lines.Count) files)"
