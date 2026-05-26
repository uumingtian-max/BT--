"""双引擎路由解析。"""

import os

import llm_dual_route as dr


def test_attachments_force_gpu(monkeypatch):
    monkeypatch.setenv("BKLT_DUAL_ENGINE", "1")
    monkeypatch.setenv("GPU_OPENAI_BASE_URL", "http://127.0.0.1:8001/v1")
    monkeypatch.setenv("GPU_OPENAI_API_KEY", "local")
    monkeypatch.setenv("GPU_MODEL", "nemotron-omni")
    monkeypatch.setenv("API_OPENAI_BASE_URL", "https://inferaichat.com/v1")
    monkeypatch.setenv("API_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("API_MODEL", "claude-opus-4-7")
    ep = dr.resolve_openai_endpoint(
        [],
        "claude-opus-4-7",
        attachments=[{"path": "C:/x.png", "filename": "x.png", "content_type": "image/png"}],
    )
    assert ep.route == "gpu"
    assert "8001" in ep.base_url


def test_text_uses_api(monkeypatch):
    monkeypatch.setenv("BKLT_DUAL_ENGINE", "1")
    monkeypatch.setenv("BKLT_LLM_DEFAULT_ROUTE", "api")
    monkeypatch.setenv("GPU_OPENAI_BASE_URL", "http://127.0.0.1:8001/v1")
    monkeypatch.setenv("GPU_MODEL", "nemotron-omni")
    monkeypatch.setenv("API_OPENAI_BASE_URL", "https://inferaichat.com/v1")
    monkeypatch.setenv("API_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("API_MODEL", "claude-opus-4-7")
    ep = dr.resolve_openai_endpoint([{"role": "user", "content": "你好"}], "claude-opus-4-7")
    assert ep.route == "api"
    assert "inferaichat" in ep.base_url
