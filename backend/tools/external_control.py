import os
import re
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from .file_ops import assert_known_user_path, resolve_user_path


def _valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+$", url or "", re.IGNORECASE))


def open_url(url: str) -> str:
    url = (url or "").strip()
    if not _valid_url(url):
        return "open_url error: 只允许打开 http:// 或 https:// URL"
    webbrowser.open(url, new=2)
    return f"Opened URL: {url}"


def open_path(path: str) -> str:
    p = resolve_user_path(path)
    if not p.exists():
        return f"open_path error: Not found: {p}"
    try:
        assert_known_user_path(p, "open_path")
    except PermissionError as exc:
        return f"open_path error: {exc}"
    if sys.platform.startswith("win"):
        os.startfile(str(p))  # noqa: S606 - local user-requested open action
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(p)])
    else:
        subprocess.Popen(["xdg-open", str(p)])
    return f"Opened path: {p}"


def get_foreground_window() -> str:
    if not sys.platform.startswith("win"):
        return "get_foreground_window error: 当前只实现 Windows 前台窗口读取。"
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "get_foreground_window error: 当前没有可读取的前台窗口。"
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value.strip()
        if not title:
            return "get_foreground_window error: 前台窗口标题为空，可能当前会话不可见。"
        return f"Foreground window: {title}"
    except Exception as exc:
        return f"get_foreground_window error: {exc}"


def _require_windows(action: str) -> str | None:
    if not sys.platform.startswith("win"):
        return f"{action} error: 当前只实现 Windows 桌面控制。"
    return None


def list_windows(limit: int = 30) -> str:
    err = _require_windows("list_windows")
    if err:
        return err
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        items: list[tuple[int, str]] = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def enum_proc(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()
            if title:
                items.append((int(hwnd), title))
            return True

        user32.EnumWindows(enum_proc, 0)
        if not items:
            return "当前没有读到可见窗口。"
        lines = ["可见窗口："]
        for hwnd, title in items[: max(1, int(limit or 30))]:
            lines.append(f"- hwnd={hwnd} | {title}")
        return "\n".join(lines)
    except Exception as exc:
        return f"list_windows error: {exc}"


def _find_window_by_title(title: str):
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    needle = (title or "").strip().lower()
    matches: list[tuple[int, str]] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_proc(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        window_title = buff.value.strip()
        if window_title and needle in window_title.lower():
            matches.append((int(hwnd), window_title))
        return True

    user32.EnumWindows(enum_proc, 0)
    return matches[0] if matches else None


def focus_window(title: str) -> str:
    err = _require_windows("focus_window")
    if err:
        return err
    title = (title or "").strip()
    if not title:
        return "focus_window error: missing title"
    try:
        import ctypes

        user32 = ctypes.windll.user32
        found = _find_window_by_title(title)
        if not found:
            return f"focus_window error: 未找到标题包含「{title}」的窗口。"
        hwnd, window_title = found
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        time.sleep(0.08)
        user32.SetForegroundWindow(hwnd)
        return f"Focused window: hwnd={hwnd} | {window_title}"
    except Exception as exc:
        return f"focus_window error: {exc}"


_VK = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "delete": 0x2E,
    "del": 0x2E,
    "win": 0x5B,
    "windows": 0x5B,
}
for i in range(1, 13):
    _VK[f"f{i}"] = 0x6F + i
for ch in "abcdefghijklmnopqrstuvwxyz0123456789":
    _VK[ch] = ord(ch.upper())


def _normalize_keys(keys) -> list[str]:
    if isinstance(keys, str):
        raw = re.split(r"\s*\+\s*|[\s,，]+", keys.strip())
    elif isinstance(keys, (list, tuple)):
        raw = [str(k) for k in keys]
    else:
        raw = []
    return [k.strip().lower() for k in raw if k and k.strip()]


def send_hotkey(keys) -> str:
    err = _require_windows("send_hotkey")
    if err:
        return err
    normalized = _normalize_keys(keys)
    if not normalized:
        return "send_hotkey error: missing keys"
    unknown = [k for k in normalized if k not in _VK]
    if unknown:
        return f"send_hotkey error: unsupported key(s): {', '.join(unknown)}"
    fg = get_foreground_window()
    if fg.startswith("get_foreground_window error:"):
        return f"send_hotkey error: {fg}"
    try:
        import ctypes

        user32 = ctypes.windll.user32
        for key in normalized:
            user32.keybd_event(_VK[key], 0, 0, 0)
            time.sleep(0.02)
        for key in reversed(normalized):
            user32.keybd_event(_VK[key], 0, 2, 0)
            time.sleep(0.02)
        return f"Sent hotkey: {'+'.join(normalized)}"
    except Exception as exc:
        return f"send_hotkey error: {exc}"


def click_screen(x: int | str, y: int | str) -> str:
    err = _require_windows("click_screen")
    if err:
        return err
    try:
        import ctypes

        fg = get_foreground_window()
        if fg.startswith("get_foreground_window error:"):
            return f"click_screen error: {fg}"
        sx = int(float(x))
        sy = int(float(y))
        user32 = ctypes.windll.user32
        user32.SetCursorPos(sx, sy)
        time.sleep(0.05)
        user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
        time.sleep(0.04)
        user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
        return f"Clicked screen coordinate: ({sx}, {sy})"
    except Exception as exc:
        return f"click_screen error: {exc}"


def type_text(text: str) -> str:
    err = _require_windows("type_text")
    if err:
        return err
    text = str(text or "")
    if not text:
        return "type_text error: missing text"
    fg = get_foreground_window()
    if fg.startswith("get_foreground_window error:"):
        return f"type_text error: {fg}"
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Set-Clipboard -Value ([Console]::In.ReadToEnd())",
            ],
            input=text,
            text=True,
            capture_output=True,
            timeout=10,
        )
        time.sleep(0.08)
        paste = send_hotkey(["ctrl", "v"])
        if "error:" in paste.lower():
            return paste
        return f"Typed text via clipboard paste ({len(text)} chars)."
    except Exception as exc:
        return f"type_text error: {exc}"
