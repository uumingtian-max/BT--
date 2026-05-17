"""SQLite connection helper with WAL enabled by default.

Import this module as ``sqlite3`` inside backend code:

    import sqlite_wal as sqlite3

It proxies the standard library sqlite3 module while wrapping connect() so every
normal connection gets WAL mode and a busy timeout. Read-only URI connections may
reject WAL pragmas, so pragma failures are intentionally ignored there.
"""

from __future__ import annotations

import sqlite3 as _sqlite3
from typing import Any


def connect(*args: Any, **kwargs: Any) -> _sqlite3.Connection:
    timeout = float(kwargs.pop("timeout", 30.0))
    conn = _sqlite3.connect(*args, timeout=timeout, **kwargs)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except _sqlite3.Error:
        pass
    try:
        conn.execute("PRAGMA busy_timeout=30000")
    except _sqlite3.Error:
        pass
    return conn


def __getattr__(name: str) -> Any:
    return getattr(_sqlite3, name)
