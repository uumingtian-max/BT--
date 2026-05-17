"""Pytest hooks: stable env before importing the FastAPI app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# backend/ is the import root (pytest.ini pythonpath = backend)
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

os.environ["REQUEST_LOG"] = "0"
os.environ["WEBHOOK_URL"] = ""

import env_bootstrap

env_bootstrap.load_backend_dotenv()
# 单测不走生产「单模型锁」，否则 /meta/models 的 Ollama mock 用例会失败
os.environ["LOCK_SINGLE_MODEL"] = "0"
os.environ["LOCKED_MODEL_ID"] = ""
os.environ["OPENAI_BASE_URL"] = ""
os.environ["OPENAI_API_KEY"] = ""
# 单测固定走 Ollama 语义，避免 backend/.env 里 vLLM / 单模型锁干扰 mock
os.environ["LLM_BACKEND"] = "ollama"
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"
os.environ["TASK_DECOMPOSE_BACKEND"] = "ollama"
os.environ["ENABLE_IMAGE_PLACEHOLDER"] = "1"
# 单测需要习惯体检 API 为启用态（CI workflow 可能设 HABIT_CHECK_ENABLED=false）
os.environ["HABIT_CHECK_ENABLED"] = "1"


@pytest.fixture(scope="module")
def client() -> TestClient:
    import main

    return TestClient(main.app)
