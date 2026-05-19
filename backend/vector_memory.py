"""Semantic memory layer (Ollama embeddings + on-disk index)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from threading import Lock
from typing import Any

from skill_pack import EMBED_MODEL, _cosine, _ollama_embed_one

INDEX_PATH = Path(__file__).resolve().parent / ".memory_vector_index.json"
_LOCK = Lock()


class VectorMemoryStore:
    """Lightweight vector store — no faiss required; cosine scan over JSON index."""

    def __init__(self) -> None:
        self.model = os.environ.get("MEMORY_EMBED_MODEL", EMBED_MODEL).strip() or EMBED_MODEL
        self.memory_map: dict[str, dict[str, Any]] = {}
        self.vectors: dict[str, list[float]] = {}
        self._load()

    def _load(self) -> None:
        if not INDEX_PATH.is_file():
            return
        try:
            data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if data.get("model") != self.model:
            return
        self.memory_map = {str(k): v for k, v in (data.get("memory_map") or {}).items()}
        self.vectors = {str(k): [float(x) for x in v] for k, v in (data.get("vectors") or {}).items()}

    def _save(self) -> None:
        payload = {
            "model": self.model,
            "updated_at": int(time.time()),
            "memory_map": self.memory_map,
            "vectors": self.vectors,
        }
        try:
            INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def add_memory(self, memory_id: int, text: str, *, category: str = "general") -> None:
        content = (text or "").strip()
        if len(content) < 4:
            return
        key = str(memory_id)
        try:
            vector = _ollama_embed_one(content[:4000])
        except Exception:
            return
        with _LOCK:
            self.memory_map[key] = {"id": memory_id, "text": content, "category": category}
            self.vectors[key] = vector
            self._save()

    def query_memory(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if len(q) < 2 or not self.vectors:
            return []
        try:
            query_vec = _ollama_embed_one(q[:2000])
        except Exception:
            return []
        scored: list[tuple[float, str]] = []
        for key, vec in self.vectors.items():
            score = _cosine(query_vec, vec)
            if score > 0.15:
                scored.append((score, key))
        scored.sort(key=lambda x: -x[0])
        out: list[dict[str, Any]] = []
        for score, key in scored[: max(1, top_k)]:
            row = self.memory_map.get(key)
            if row:
                out.append({**row, "vector_score": round(score, 4)})
        return out


_STORE: VectorMemoryStore | None = None


def get_vector_memory_store() -> VectorMemoryStore:
    global _STORE
    if _STORE is None:
        _STORE = VectorMemoryStore()
    return _STORE


def vector_memory_enabled() -> bool:
    return os.environ.get("MEMORY_VECTOR_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")
