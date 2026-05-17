from pathlib import Path

from content_pipeline import process_content


def test_process_text_to_report(tmp_path):
    result = process_content(
        source="BKLT 黑光可以把任意公开内容整理成报告、PPT 大纲、思维导图和 Quiz。\n\n第二段：内容会先清洗，再输出到 outputs/content_pipeline。",
        source_type="text",
        output_type="report",
        title="BKLT 内容管线测试",
        ingest=False,
    )
    assert result["ok"] is True
    assert result["output_type"] == "report"
    assert result["output_path"].endswith("-report.md")
    assert Path(result["output_path"]).is_absolute() is False


def test_process_text_to_quiz():
    result = process_content(
        source="第一点：输入可以是文本。\n\n第二点：输出可以是 quiz。",
        source_type="text",
        output_type="quiz",
        title="Quiz 测试",
        ingest=False,
    )
    assert result["ok"] is True
    assert result["output_type"] == "quiz"
    assert "Quiz" in result["preview"]
    assert "答案" in result["preview"]
