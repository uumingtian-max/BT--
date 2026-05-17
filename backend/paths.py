"""项目根路径（目录整理后统一由此解析）。"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VAULT_DIR = DATA_DIR / "knowledge-vault"
LEGACY_VAULT_DIR = PROJECT_ROOT / "knowledge-vault"


def legacy_agent_db_path() -> Path:
    env = os.environ.get("LOCAL_AGENT_ROOT", "").strip()
    base = Path(env).resolve() if env else PROJECT_ROOT
    primary = base / "data" / "agent_tasks.db"
    if primary.is_file():
        return primary
    fallback = base / "agent_tasks.db"
    return fallback if fallback.is_file() else primary
