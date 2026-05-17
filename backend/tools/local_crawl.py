"""Local Firecrawl-lite tools: no API key, no cloud dependency."""

from __future__ import annotations

import html
import os
import re
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

from .search import web_search

MAX_SCRAPE_BYTES = int(os.environ.get("AGENT_SCRAPE_MAX_BYTES", str(2 * 1024 * 1024)))


class _ReadableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []
        self._skip_depth = 0
        self._last_tag = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        self._last_tag = tag
        if tag in {"script", "style", "noscript", "svg", "canvas"}:
            self._skip_depth += 1
            return
        if tag in {
            "p",
            "div",
            "section",
            "article",
            "br",
            "li",
            "tr",
            "h1",
            "h2",
            "h3",
        }:
            self.parts.append("\n")
        if tag == "a":
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.links.append(str(value))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "canvas"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = html.unescape(data or "").strip()
        if not text:
            return
        if self._last_tag in {"h1", "h2", "h3"}:
            self.parts.append(f"\n## {text}\n")
        else:
            self.parts.append(text + " ")

    def readable_text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _valid_url(url: str) -> bool:
    parsed = urlparse(url or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def local_scrape_url(url: str, max_chars: int = 12000) -> str:
    url = (url or "").strip()
    if not _valid_url(url):
        return "local_scrape_url error: 只支持 http/https URL"
    try:
        with httpx.Client(
            timeout=25,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AIAgent/1.0"},
        ) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                content_length = resp.headers.get("content-length")
                if content_length and content_length.isdigit() and int(content_length) > MAX_SCRAPE_BYTES:
                    return f"local_scrape_url error: response too large ({content_length} bytes > {MAX_SCRAPE_BYTES})"
                data = bytearray()
                for chunk in resp.iter_bytes():
                    if not chunk:
                        continue
                    data.extend(chunk)
                    if len(data) > MAX_SCRAPE_BYTES:
                        return f"local_scrape_url error: response exceeded {MAX_SCRAPE_BYTES} bytes"
                raw_html = bytes(data).decode(resp.encoding or "utf-8", errors="replace")
        parser = _ReadableHTMLParser()
        parser.feed(raw_html)
        text = parser.readable_text()
        if not text:
            return f"local_scrape_url error: 页面没有提取到可读文本: {url}"
        title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.I | re.S)
        title = re.sub(r"\s+", " ", html.unescape(title_match.group(1))).strip() if title_match else url
        body = text[: max(1000, int(max_chars or 12000))]
        if len(text) > len(body):
            body += "\n\n...[truncated]"
        return f"# {title}\n\nURL: {url}\n\n{body}"
    except Exception as exc:
        return f"local_scrape_url error: {exc}"


def local_search(query: str, limit: int = 6, scrape: bool = False) -> str:
    q = (query or "").strip()
    if not q:
        return "local_search error: missing query"
    raw = web_search(q)
    urls = re.findall(r"https?://[^\s)>\]]+", raw)
    lines = [raw.strip()]
    if scrape and urls:
        lines.append("\n\n## 抓取结果")
        for url in urls[: max(1, int(limit or 3))]:
            lines.append(local_scrape_url(url, max_chars=5000))
    return "\n\n".join(part for part in lines if part)
