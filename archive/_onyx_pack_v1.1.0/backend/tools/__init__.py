"""Agent tools package (search, crawl, files, code, desktop control, browser)."""

from .code_exec import execute_python
from .external_control import (
    click_screen,
    focus_window,
    get_foreground_window,
    list_windows,
    open_path,
    open_url,
    send_hotkey,
    type_text,
)
from .file_ops import list_files, read_file, resolve_user_path, write_file
from .local_crawl import local_scrape_url, local_search
from .search import web_search
from .browser import (
    browser_click_and_extract,
    browser_fill_form,
    browser_navigate,
    browser_playwright,
    browser_screenshot,
)

__all__ = [
    "web_search",
    "local_search",
    "local_scrape_url",
    "read_file",
    "write_file",
    "list_files",
    "resolve_user_path",
    "execute_python",
    "open_url",
    "open_path",
    "get_foreground_window",
    "list_windows",
    "focus_window",
    "send_hotkey",
    "type_text",
    "click_screen",
    "browser_navigate",
    "browser_playwright",
    "browser_screenshot",
    "browser_click_and_extract",
    "browser_fill_form",
]
