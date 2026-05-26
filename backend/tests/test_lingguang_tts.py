"""灵光 / Edge TTS 解析与健康检查。"""

import asyncio
import base64

import lingguang_tts as lt


def test_resolve_voice_aliases():
    assert lt.resolve_voice("alipay_lingguang") == "zh-CN-XiaoyiNeural"
    assert lt.resolve_voice("灵光") == "zh-CN-XiaoyiNeural"
    assert lt.resolve_voice("zh-CN-YunxiNeural") == "zh-CN-YunxiNeural"


def test_normalize_text_b64():
    raw = "黑光已就位"
    b64 = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    assert lt.normalize_request_text("", b64) == raw


def test_health_reports_engine():
    h = lt.health_status()
    assert "engine" in h
    assert h["default_voice"] == "zh-CN-XiaoyiNeural"


def test_cli_file_synthesis():
    data, err = lt._synthesize_via_cli_file("测试", "zh-CN-XiaoyiNeural")
    assert err is None
    assert len(data) > 1000


def test_async_synthesis():
    data, err = asyncio.run(lt.synthesize_mp3_async("黑光已就位", "alipay_lingguang"))
    assert err is None
    assert len(data) > 1000
