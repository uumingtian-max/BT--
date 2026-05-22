from __future__ import annotations

from pathlib import Path

import pytest

from mm_openai_payload import (
    apply_multimodal_to_messages,
    build_user_content,
    normalize_attachments,
    strip_legacy_attachment_prompt,
    win_path_to_vllm_file_url,
)


def test_strip_legacy_attachment_prompt():
    msg = "请分析\n\n[上传附件]\n1. a.mp4 | video/mp4 | local_path=C:\\x\\a.mp4"
    assert "[上传附件]" not in strip_legacy_attachment_prompt(msg)
    assert strip_legacy_attachment_prompt(msg).startswith("请分析")


def test_normalize_attachments():
    raw = [{"path": "C:\\a.png", "filename": "a.png", "content_type": "image/png"}]
    assert len(normalize_attachments(raw)) == 1


def test_win_path_to_vllm_file_url(tmp_path: Path):
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    url = win_path_to_vllm_file_url(str(f))
    assert url.startswith("file:///mnt/")


def test_build_user_content_multipart(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AGENT_OMNI_MM_ENABLED", "1")
    atts = [{"path": "C:\\fake\\x.png", "content_type": "image/png"}]
    monkeypatch.setattr(
        "mm_openai_payload.win_path_to_vllm_file_url",
        lambda p: "file:///mnt/c/fake/x.png",
    )
    content = build_user_content("看一下", atts)
    assert isinstance(content, list)
    assert any(p.get("type") == "image_url" for p in content)


def test_apply_multimodal_structured_attachments(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AGENT_OMNI_MM_ENABLED", "1")
    monkeypatch.setattr(
        "mm_openai_payload.win_path_to_vllm_file_url",
        lambda p: "file:///mnt/c/fake/x.png",
    )
    msgs = [
        {"role": "user", "content": "分析", "attachments": [{"path": "C:\\fake\\x.png", "content_type": "image/png"}]},
    ]
    out = apply_multimodal_to_messages(msgs)
    assert isinstance(out[0]["content"], list)
