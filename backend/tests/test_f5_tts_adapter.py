from __future__ import annotations

import pytest
from fastapi import HTTPException


def test_f5_rate_to_speed() -> None:
    from f5_tts_server import _rate_to_speed

    assert _rate_to_speed("+0%") == pytest.approx(1.0)
    assert _rate_to_speed("-6%") == pytest.approx(0.94)
    assert _rate_to_speed("+99%") == pytest.approx(1.18)
    assert _rate_to_speed("-99%") == pytest.approx(0.82)


def test_f5_text_cleanup_and_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    from f5_tts_server import F5TTSRequest, _natural_gen_text

    monkeypatch.setenv("F5_TTS_MAX_CHARS", "80")
    text = _natural_gen_text(F5TTSRequest(text="  你好，   今天我们慢慢聊。 " * 8))
    assert "\n" not in text
    assert "   " not in text
    assert len(text) <= 80


def test_f5_ref_audio_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    from f5_tts_server import F5TTSRequest, _project_root, _resolve_ref_audio

    # _resolve_ref_audio joins relative paths to the repo root, not pytest cwd.
    ref = "outputs/f5-test-ref.wav"
    path = _project_root() / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFFfake")
    try:
        monkeypatch.setenv("F5_TTS_REF_AUDIO", ref)
        assert _resolve_ref_audio(F5TTSRequest(text="hi")).name == path.name
    finally:
        path.unlink(missing_ok=True)


def test_f5_ref_audio_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    from f5_tts_server import F5TTSRequest, _resolve_ref_audio

    monkeypatch.delenv("F5_TTS_REF_AUDIO", raising=False)
    with pytest.raises(HTTPException) as exc:
        _resolve_ref_audio(F5TTSRequest(text="hi"))
    assert exc.value.status_code == 400
