$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venv = Join-Path $root ".venv-f5"
$py = Join-Path $venv "Scripts\python.exe"

Set-Location $root

if (!(Test-Path $py)) {
  python -m venv $venv
}

& $py -m pip install --upgrade pip setuptools wheel
& $py -m pip install f5-tts

Write-Host ""
Write-Host "[ONYX] F5-TTS installed."
Write-Host "[ONYX] Put your authorized reference audio at: outputs\voice_ref.wav"
Write-Host "[ONYX] Set F5_TTS_REF_TEXT in backend\.env, then run START_F5_TTS.bat"
