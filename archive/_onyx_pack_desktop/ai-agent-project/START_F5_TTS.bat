@echo off
setlocal
cd /d "%~dp0"
echo.
echo [ONYX] Starting local F5-TTS adapter for mobile voice...
echo [ONYX] URL: http://127.0.0.1:9880/tts
echo.
echo Configure first:
echo   F5_TTS_REF_AUDIO=outputs\voice_ref.wav
echo   F5_TTS_REF_TEXT=the exact words in that reference audio
echo.
set HF_ENDPOINT=https://huggingface.co
set HUGGINGFACE_HUB_BASE_URL=https://huggingface.co
if exist "%~dp0.venv-f5\Scripts\python.exe" (
  "%~dp0.venv-f5\Scripts\python.exe" -m uvicorn backend.f5_tts_server:app --host 127.0.0.1 --port 9880
) else (
  python -m uvicorn backend.f5_tts_server:app --host 127.0.0.1 --port 9880
)
pause
