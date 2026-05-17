"""Local Anything-to-Notebook style content pipeline for BKLT.

This module intentionally implements the safe/local subset of the
Anything -> NotebookLM idea:

- public URL text extraction through the existing local scraper
- local file or pasted text ingestion
- deterministic outputs: report, slide outline, mind map, quiz, podcast script
- optional local knowledge-base ingestion

It does not bypass login, subscription, paywall, or access-control barriers.
External NotebookLM upload/generation should be implemented as a separate
confirm-level tool because it sends user content to a third-party service.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from memory_store import ingest_notebook_corpus
from tools.file_ops import read_file
from tools.local_crawl import local_scrape_url

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "outputs" / "content_pipeline"

OutputType = Literal["report", "slides", "mindmap", "quiz", "podcast_script", "notes"]
SourceType = Literal["auto", "url", "path", "text"]


@dataclass
class ContentSource:
    source_type: SourceType
    source: str
    title: str
    text: str


def process_content(
    *,
    source: str,
    source_type: SourceType = "auto",
    output_type: OutputType = "report",
    title: str | None = None,
    ingest: bool = False,
) -> dict:
    """Process one content source and write a markdown artifact."""
    normalized_output = _normalize_output_type(output_type)
    content = _load_source(source=source, source_type=source_type, title=title)
    sections = _extract_sections(content.text)
    artifact_text = _render_output(content, sections, normalized_output)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / _artifact_name(content.title, normalized_output)
    out_path.write_text(artifact_text, encoding="utf-8")

    ingest_result = None
    if ingest:
        ingest_result = ingest_notebook_corpus(f"{content.title} · {normalized_output}", artifact_text)

    return {
        "ok": True,
        "source_type": content.source_type,
        "source": content.source,
        "title": content.title,
        "output_type": normalized_output,
        "output_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        "chars": len(content.text),
        "sections": len(sections),
        "ingest": ingest_result,
        "preview": artifact_text[:1200],
    }


def _normalize_output_type(value: str | None) -> OutputType:
    raw = (value or "report").strip().lower().replace("-", "_")
    aliases = {
        "ppt": "slides",
        "slide": "slides",
        "slide_deck": "slides",
        "mind_map": "mindmap",
        "map": "mindmap",
        "audio": "podcast_script",
        "podcast": "podcast_script",
        "script": "podcast_script",
        "note": "notes",
        "summary": "notes",
    }
    raw = aliases.get(raw, raw)
    allowed = {"report", "slides", "mindmap", "quiz", "podcast_script", "notes"}
    if raw not in allowed:
        raise ValueError(f"unsupported output_type: {value}")
    return raw  # type: ignore[return-value]


def _load_source(*, source: str, source_type: SourceType, title: str | None) -> ContentSource:
    src = (source or "").strip()
    if not src:
        raise ValueError("source is required")
    st = _detect_source_type(src, source_type)
    if st == "url":
        text = local_scrape_url(src, max_chars=40000)
        if _looks_unreadable(text):
            raise ValueError("URL content could not be read. Ask the user for a screenshot or pasted text.")
        final_title = title or _title_from_url(src) or _title_from_text(text)
        return ContentSource("url", src, final_title, text)
    if st == "path":
        text = read_file(src)
        if text.lower().startswith("not found") or text.lower().startswith("read_file error"):
            raise ValueError(text)
        final_title = title or Path(src).stem or _title_from_text(text)
        return ContentSource("path", src, final_title, text)
    final_title = title or _title_from_text(src)
    return ContentSource("text", "pasted_text", final_title, src)


def _detect_source_type(source: str, source_type: SourceType) -> SourceType:
    if source_type != "auto":
        return source_type
    if re.match(r"https?://", source, re.IGNORECASE):
        return "url"
    if re.match(r"^[A-Za-z]:[\\/]", source) or source.startswith(("~/", "/", ".\\", "./")):
        return "path"
    return "text"


def _looks_unreadable(text: str) -> bool:
    low = (text or "").lower()
    blocked_markers = [
        "login",
        "sign in",
        "enable javascript",
        "access denied",
        "captcha",
        "403",
        "401",
    ]
    return len((text or "").strip()) < 120 or any(m in low for m in blocked_markers)


def _title_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "") or "url"
    tail = Path(parsed.path).stem[:60]
    return tail or host


def _title_from_text(text: str) -> str:
    for line in (text or "").splitlines():
        s = line.strip().lstrip("# ").strip()
        if 4 <= len(s) <= 80:
            return s
    return "content"


def _extract_sections(text: str) -> list[dict[str, object]]:
    clean = re.sub(r"\n{3,}", "\n\n", text or "").strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean) if p.strip()]
    if not paragraphs:
        paragraphs = [clean[:1200]] if clean else []
    sections = []
    for i, para in enumerate(paragraphs[:12], 1):
        title = _section_title(para, i)
        bullets = _bulletize(para)
        sections.append(
            {
                "title": title,
                "summary": _compress_sentence(para, 260),
                "bullets": bullets,
            }
        )
    return sections


def _section_title(text: str, index: int) -> str:
    first = text.splitlines()[0].strip().lstrip("# ").strip()
    first = re.sub(r"^[\-*>\d\.\s]+", "", first)
    if 4 <= len(first) <= 60:
        return first
    return f"要点 {index}"


def _compress_sentence(text: str, limit: int) -> str:
    s = re.sub(r"\s+", " ", text or "").strip()
    if len(s) <= limit:
        return s
    return s[:limit].rstrip() + "..."


def _bulletize(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith(("- ", "* ")):
            lines.append(s[2:].strip())
        elif re.match(r"^\d+[\.、]\s+", s):
            lines.append(re.sub(r"^\d+[\.、]\s+", "", s))
    if not lines:
        chunks = re.split(r"(?<=[。！？.!?])\s*", re.sub(r"\s+", " ", text.strip()))
        lines = [c.strip() for c in chunks if len(c.strip()) >= 18]
    return [_compress_sentence(x, 140) for x in lines[:5]]


def _render_output(source: ContentSource, sections: list[dict[str, object]], output_type: OutputType) -> str:
    header = _artifact_header(source, output_type)
    if output_type == "slides":
        return header + _render_slides(source, sections)
    if output_type == "mindmap":
        return header + _render_mindmap(source, sections)
    if output_type == "quiz":
        return header + _render_quiz(source, sections)
    if output_type == "podcast_script":
        return header + _render_podcast(source, sections)
    if output_type == "notes":
        return header + _render_notes(source, sections)
    return header + _render_report(source, sections)


def _artifact_header(source: ContentSource, output_type: OutputType) -> str:
    return (
        f"# {source.title}\n\n"
        f"- 输出类型：`{output_type}`\n"
        f"- 来源类型：`{source.source_type}`\n"
        f"- 来源：`{source.source}`\n"
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "---\n\n"
    )


def _render_report(source: ContentSource, sections: list[dict[str, object]]) -> str:
    lines = ["## 一句话结论", "", _one_line_takeaway(sections), "", "## 结构化报告", ""]
    for sec in sections:
        lines.append(f"### {sec['title']}")
        lines.append(str(sec["summary"]))
        for item in sec["bullets"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(
        [
            "## 行动建议",
            "",
            "- 把关键结论写入 BKLT 知识库。",
            "- 如需演示，继续用 slides 输出生成 PPT 大纲。",
            "- 如需复习，继续用 quiz 输出生成题库。",
            "",
        ]
    )
    return "\n".join(lines)


def _render_notes(source: ContentSource, sections: list[dict[str, object]]) -> str:
    lines = ["## 笔记", ""]
    for sec in sections:
        lines.append(f"- **{sec['title']}**：{sec['summary']}")
    return "\n".join(lines) + "\n"


def _render_slides(source: ContentSource, sections: list[dict[str, object]]) -> str:
    lines = [
        "## PPT 大纲",
        "",
        "### Slide 1：标题",
        f"- {source.title}",
        "- BKLT 黑光自动整理",
        "",
    ]
    for i, sec in enumerate(sections[:10], 2):
        lines.append(f"### Slide {i}：{sec['title']}")
        lines.append(f"- {sec['summary']}")
        for item in sec["bullets"][:3]:
            lines.append(f"- {item}")
        lines.append("")
    lines.append(f"### Slide {min(len(sections) + 2, 12)}：结论与下一步")
    lines.append(f"- {_one_line_takeaway(sections)}")
    lines.append("- 下一步：落地为任务、技能或知识库条目。")
    return "\n".join(lines) + "\n"


def _render_mindmap(source: ContentSource, sections: list[dict[str, object]]) -> str:
    lines = [
        "## Mermaid 思维导图",
        "",
        "```mermaid",
        "mindmap",
        f"  root(({_escape_mermaid(source.title)}))",
    ]
    for sec in sections[:8]:
        lines.append(f"    {_escape_mermaid(str(sec['title']))}")
        for item in sec["bullets"][:3]:
            lines.append(f"      {_escape_mermaid(str(item))}")
    lines.extend(["```", ""])
    return "\n".join(lines)


def _render_quiz(source: ContentSource, sections: list[dict[str, object]]) -> str:
    lines = ["## Quiz", ""]
    for i, sec in enumerate(sections[:10], 1):
        answer = str(sec["summary"])
        lines.append(f"### Q{i}. {sec['title']} 的核心意思是什么？")
        lines.append("A. 与主题无关的背景信息")
        lines.append(f"B. {answer[:90]}")
        lines.append("C. 只是一条待办提醒")
        lines.append("D. 无法从材料中判断")
        lines.append("")
        lines.append("**答案：B**")
        lines.append(f"**解析：** {answer}")
        lines.append("")
    return "\n".join(lines)


def _render_podcast(source: ContentSource, sections: list[dict[str, object]]) -> str:
    lines = ["## 播客脚本", "", "**开场**", f"今天我们聊的是：{source.title}。", ""]
    for sec in sections[:8]:
        lines.append(f"**段落：{sec['title']}**")
        lines.append(str(sec["summary"]))
        for item in sec["bullets"][:2]:
            lines.append(f"可以这样理解：{item}")
        lines.append("")
    lines.append("**结尾**")
    lines.append(_one_line_takeaway(sections))
    return "\n".join(lines) + "\n"


def _one_line_takeaway(sections: list[dict[str, object]]) -> str:
    if not sections:
        return "材料内容较少，建议补充更多上下文后再整理。"
    first = sections[0]
    return f"核心是：{first['summary']}"


def _artifact_name(title: str, output_type: OutputType) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", title).strip("_")[:48] or "content"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{slug}-{output_type}.md"


def _escape_mermaid(text: str) -> str:
    s = re.sub(r"[(){}[\]<>]", " ", text)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:80] or "节点"
