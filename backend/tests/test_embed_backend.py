from __future__ import annotations

from unittest.mock import patch

import embed_backend


def test_embed_backend_name_default(monkeypatch):
    monkeypatch.delenv("EMBED_BACKEND", raising=False)
    assert embed_backend.embed_backend_name() == "ollama"


def test_embed_backend_name_openvino(monkeypatch):
    monkeypatch.setenv("EMBED_BACKEND", "openvino")
    assert embed_backend.embed_backend_name() == "openvino"


def test_embed_one_uses_ollama_when_not_openvino(monkeypatch):
    monkeypatch.setenv("EMBED_BACKEND", "ollama")
    with patch.object(embed_backend, "_ollama_embed_one", return_value=[0.1, 0.2]) as m:
        out = embed_backend.embed_one("hi")
    assert out == [0.1, 0.2]
    m.assert_called_once_with("hi")


def test_embed_one_openvino_fallback_to_ollama(monkeypatch):
    monkeypatch.setenv("EMBED_BACKEND", "openvino")
    with patch.object(
        embed_backend,
        "_openvino_embed_one",
        side_effect=RuntimeError("npu busy"),
    ):
        with patch.object(
            embed_backend,
            "_ollama_embed_one",
            return_value=[1.0, 0.0],
        ) as m:
            out = embed_backend.embed_one("hi")
    assert out == [1.0, 0.0]
    m.assert_called_once_with("hi")


def test_l2_normalize():
    assert embed_backend._l2_normalize([3.0, 4.0]) == [0.6, 0.8]
