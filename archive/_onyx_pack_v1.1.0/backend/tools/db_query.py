"""SQLite 只读查询（Agent / 工具面板）。"""

from __future__ import annotations

import sqlite_wal as sqlite3
from pathlib import Path

from tools.file_ops import resolve_user_path


def query_database(path: str, sql: str, limit: int = 50) -> str:
    db_path = resolve_user_path((path or "").strip())
    if not db_path:
        return "query_database error: 缺少数据库路径 path"
    p = Path(db_path)
    if not p.is_file():
        return f"query_database error: 文件不存在 {p}"
    sql = (sql or "").strip().rstrip(";")
    if not sql:
        return "query_database error: 缺少 sql"
    lowered = sql.lower()
    if not lowered.startswith("select"):
        return "query_database error: 仅允许 SELECT 只读查询"
    forbidden = ("insert", "update", "delete", "drop", "alter", "attach", "pragma")
    if any(word in lowered for word in forbidden):
        return "query_database error: SQL 含不允许的关键字"
    limit = max(1, min(200, int(limit or 50)))
    try:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql)
        rows = cur.fetchmany(limit + 1)
        conn.close()
        if not rows:
            return "(0 rows)"
        truncated = len(rows) > limit
        rows = rows[:limit]
        cols = rows[0].keys()
        lines = ["\t".join(cols)]
        for row in rows:
            lines.append("\t".join(str(row[c]) for c in cols))
        out = "\n".join(lines)
        if truncated:
            out += f"\n…(仅显示前 {limit} 行)"
        if len(out) > 12000:
            out = out[:12000] + "\n…(truncated)"
        return out
    except Exception as e:
        return f"query_database error: {e}"
