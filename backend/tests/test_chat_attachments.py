from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_chat_rejects_attachments_when_vllm_down(client: TestClient) -> None:
    with patch("mm_openai_payload.check_vllm_gateway_ready", return_value=(False, "vLLM 未启动")):
        r = client.post(
            "/chat/",
            json={
                "session_id": "att-test",
                "message": "分析视频",
                "model": "test",
                "stream": False,
                "attachments": [
                    {
                        "path": r"C:\fake\clip.mp4",
                        "filename": "clip.mp4",
                        "content_type": "video/mp4",
                    }
                ],
            },
        )
    assert r.status_code == 503
    assert "vLLM" in (r.json().get("detail") or "")
