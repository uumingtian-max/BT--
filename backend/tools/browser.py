"""Playwright browser automation (optional: pip install playwright && playwright install chromium)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from safe_paths import safe_output_path


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


def _normalize_playwright_env() -> None:
    raw = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    if "%LOCALAPPDATA%" in raw:
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = raw.replace("%LOCALAPPDATA%", local)


def _ensure_playwright() -> None:
    _normalize_playwright_env()
    if _playwright_available():
        return
    raise RuntimeError(
        "Playwright is not installed. Browser automation is disabled until the user explicitly approves "
        "`pip install playwright` and `python -m playwright install chromium`."
    )


def browser_navigate(url: str, wait_ms: int = 2000, screenshot: bool = False) -> str:
    _normalize_playwright_env()
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return "browser_navigate error: 只支持 http/https URL"
    if not _playwright_available():
        _ensure_playwright()
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(max(0, int(wait_ms)))
            content = (page.inner_text("body") or "")[:8000]
            result: dict = {"url": url, "content": content[:4000]}
            if screenshot:
                out = Path(__file__).resolve().parents[2] / "outputs" / "browser_nav.png"
                out.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(out), full_page=False)
                result["screenshot_path"] = str(out)
            browser.close()
            return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f"browser_navigate error: {e}"


def browser_click_and_extract(url: str, selector: str, extract_selector: str = "body") -> str:
    _normalize_playwright_env()
    url = (url or "").strip()
    selector = (selector or "").strip()
    if not url or not selector:
        return "browser_click_and_extract error: 需要 url 与 selector"
    if not _playwright_available():
        _ensure_playwright()
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(1500)
            page.click(selector, timeout=10000)
            page.wait_for_timeout(1500)
            content = (page.inner_text(extract_selector or "body") or "")[:6000]
            browser.close()
            return content
    except Exception as e:
        return f"browser_click_and_extract error: {e}"


def browser_fill_form(url: str, fields: dict, submit_selector: str | None = None) -> str:
    _normalize_playwright_env()
    url = (url or "").strip()
    if not url or not isinstance(fields, dict) or not fields:
        return "browser_fill_form error: 需要 url 与 fields 对象"
    if not _playwright_available():
        _ensure_playwright()
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(1500)
            for sel, value in fields.items():
                raw = str(sel).strip()
                candidates = [raw]
                if not raw.startswith(("#", ".", "[", "input", "textarea", "select")):
                    candidates = [
                        f'[name="{raw}"]',
                        f"#{raw}",
                        f'input[name="{raw}"]',
                        f'textarea[name="{raw}"]',
                        f'select[name="{raw}"]',
                    ]
                filled = False
                for candidate in candidates:
                    try:
                        page.fill(candidate, str(value), timeout=3000)
                        filled = True
                        break
                    except Exception:
                        continue
                if not filled:
                    browser.close()
                    return f"browser_fill_form error: 未找到字段 {raw}"
            if submit_selector:
                page.click(str(submit_selector))
                page.wait_for_timeout(2000)
            result = (page.inner_text("body") or "")[:4000]
            browser.close()
            return f"表单已填写并提交。页面响应：\n{result}"
    except Exception as e:
        return f"browser_fill_form error: {e}"


def browser_screenshot(url: str, output_path: str = "outputs/browser_shot.png") -> str:
    _normalize_playwright_env()
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return "browser_screenshot error: 只支持 http/https URL"
    if not _playwright_available():
        _ensure_playwright()
    try:
        from playwright.sync_api import sync_playwright

        out = safe_output_path(output_path, default_name="browser_shot.png")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            page.screenshot(path=str(out), full_page=True)
            browser.close()
            return f"截图已保存到 {out}"
    except Exception as e:
        return f"browser_screenshot error: {e}"


def browser_playwright(
    url: str,
    action: str = "navigate",
    selector: str = "",
    text: str = "",
    extract_selector: str = "body",
    output_path: str = "outputs/browser_shot.png",
    wait_ms: int = 2000,
) -> str:
    """Unified Playwright tool used by skills that reference browser_playwright."""
    action = (action or "navigate").strip().lower()
    if action in {"navigate", "open", "goto", "extract", "read"}:
        return browser_navigate(url, wait_ms=wait_ms, screenshot=False)
    if action in {"screenshot", "shot", "capture"}:
        return browser_screenshot(url, output_path=output_path)
    if action in {"click", "click_and_extract"}:
        return browser_click_and_extract(url, selector, extract_selector=extract_selector)
    if action in {"fill", "fill_form", "submit"}:
        fields = {selector: text} if selector else {}
        return browser_fill_form(url, fields)
    if action in {"vision_click", "vla_click"}:
        return browser_vision_action(url, selector=selector, text=text, wait_ms=wait_ms)
    return f"browser_playwright error: action 必须是 navigate/screenshot/click/fill/vision_click 之一；收到 {action!r}"


def browser_vision_action(
    url: str,
    *,
    selector: str = "",
    text: str = "",
    wait_ms: int = 2000,
) -> str:
    """VLA-lite: screenshot + element box + optional click/type (Vision-Language-Action)."""
    _normalize_playwright_env()
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return json.dumps({"ok": False, "error": "需要 http/https URL"}, ensure_ascii=False)
    if not _playwright_available():
        _ensure_playwright()
    try:
        from playwright.sync_api import sync_playwright

        out = safe_output_path("outputs/browser_vla.png", default_name="browser_vla.png")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, timeout=30000)
            page.wait_for_timeout(max(0, int(wait_ms)))
            action_trace: list[dict[str, str | int]] = []
            box: dict[str, float] | None = None
            if selector:
                el = page.query_selector(selector)
                if el:
                    box = el.bounding_box()
                    el.click(timeout=8000)
                    action_trace.append({"op": "click", "selector": selector})
                    if text:
                        page.keyboard.type(text[:500])
                        action_trace.append({"op": "type", "chars": len(text[:500])})
            page.screenshot(path=str(out), full_page=False)
            browser.close()
        payload = {
            "ok": True,
            "url": url,
            "screenshot_path": str(out),
            "viewport": {"width": 1280, "height": 800},
            "element_box": box,
            "trace": action_trace,
            "hint": "前端上帝视角可展示 screenshot_path 与 element_box 光标轨迹",
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
