"""
Trend-aligned skill snippets (markdown) loaded from backend/agent_skills/*.md.
Community pattern: explicit triggers + compact playbooks (skills repos, managed agents, MCP-style context).
"""

from __future__ import annotations

import re
import json
import hashlib
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

import httpx

from agent_runtime import get_runtime

SKILL_DIR = Path(__file__).resolve().parent / "agent_skills"
EMBED_INDEX_PATH = Path(__file__).resolve().parent / ".skill_embedding_index.json"
EMBED_MODEL = os.environ.get("SKILL_EMBED_MODEL", "nomic-embed-text").strip() or "nomic-embed-text"
EMBED_TIMEOUT_SEC = float(os.environ.get("SKILL_EMBED_TIMEOUT_SEC", "8") or "8")
_SKILL_CACHE_LOCK = Lock()
_SKILL_CACHE: dict[str, object] = {"signature": None, "skills": []}
_EMBED_CACHE_LOCK = Lock()
_EMBED_FAILURE_UNTIL = 0.0


@dataclass(frozen=True)
class SkillDoc:
    stem: str
    title: str
    triggers: tuple[str, ...]
    body: str


def _parse_skill_file(path: Path) -> SkillDoc | None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    title = path.stem.replace("_", " ")
    triggers: list[str] = []
    body_lines: list[str] = []
    for line in lines:
        ls = line.strip()
        low = ls.lower()
        if low.startswith("triggers:"):
            rest = ls.split(":", 1)[1] if ":" in ls else ""
            triggers.extend(t.strip() for t in re.split(r"[,，]", rest) if t.strip())
            continue
        if ls.startswith("# ") and not ls.startswith("##"):
            title = ls[2:].strip()
            continue
        if ls == "---":
            continue
        body_lines.append(line)
    body = "\n".join(body_lines).strip()
    if not body:
        return None
    if not triggers:
        triggers = [path.stem.lower()]
    return SkillDoc(stem=path.stem, title=title, triggers=tuple(triggers), body=body)


def _load_all_skills() -> list[SkillDoc]:
    if not SKILL_DIR.is_dir():
        return []
    paths = sorted(SKILL_DIR.glob("*.md"))
    signature = tuple((path.name, (st := path.stat()).st_mtime_ns, st.st_size) for path in paths)
    cached_signature = _SKILL_CACHE.get("signature")
    cached_skills = _SKILL_CACHE.get("skills")
    if cached_signature == signature and isinstance(cached_skills, list):
        return cached_skills
    with _SKILL_CACHE_LOCK:
        cached_signature = _SKILL_CACHE.get("signature")
        cached_skills = _SKILL_CACHE.get("skills")
        if cached_signature == signature and isinstance(cached_skills, list):
            return cached_skills
        out: list[SkillDoc] = []
        for path in paths:
            try:
                doc = _parse_skill_file(path)
                if doc:
                    out.append(doc)
            except OSError:
                continue
        _SKILL_CACHE["signature"] = signature
        _SKILL_CACHE["skills"] = out
        return out


def invalidate_skill_cache() -> None:
    with _SKILL_CACHE_LOCK:
        _SKILL_CACHE["signature"] = None
        _SKILL_CACHE["skills"] = []
    with _EMBED_CACHE_LOCK:
        global _EMBED_FAILURE_UNTIL
        _EMBED_FAILURE_UNTIL = 0.0


def list_skills_meta() -> list[dict[str, object]]:
    """技能目录（供 /meta/skills 与前端技能库）。"""
    return [
        {
            "id": sk.stem,
            "title": sk.title,
            "triggers": list(sk.triggers),
            "chars": len(sk.body),
        }
        for sk in _load_all_skills()
    ]


def _forced_skill_stem(message: str) -> tuple[str | None, str]:
    m = re.match(r"^\[skill:([a-zA-Z0-9_-]+)\]\s*", message or "")
    if not m:
        return None, message
    return m.group(1), message[m.end() :].lstrip()


def _message_tokens(text: str) -> set[str]:
    low = (text or "").lower()
    tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|[a-z][a-z0-9_-]{2,}", low))
    tokens.update(w for w in re.split(r"\s+", low) if len(w) >= 3)
    return tokens


def _score_skill(sk: SkillDoc, text: str, tokens: set[str]) -> int:
    score = 0
    for t in sk.triggers:
        tl = t.lower().strip()
        if not tl:
            continue
        if tl in text:
            score += 3 if len(tl) >= 5 else 2
        elif len(tl) >= 4 and any(tl in tok or tok in tl for tok in tokens):
            score += 1
    stem_bits = sk.stem.replace("_", " ").lower().split()
    for bit in stem_bits:
        if len(bit) >= 4 and bit in text:
            score += 1
    if sk.stem.startswith("tool_") and sk.stem[5:].replace("_", " ") in text:
        score += 2
    return score


def _skill_signature(skills: list[SkillDoc]) -> list[list[Any]]:
    return [
        [
            sk.stem,
            sk.title,
            len(sk.body),
            hashlib.sha256(sk.body.encode("utf-8")).hexdigest(),
        ]
        for sk in skills
    ]


def _skill_embedding_text(sk: SkillDoc) -> str:
    triggers = ", ".join(sk.triggers)
    body = sk.body[:1800]
    return f"{sk.title}\nid:{sk.stem}\ntriggers:{triggers}\n{body}"


def _ollama_base_url() -> str:
    base = os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434"
    return base.rstrip("/")


def _ollama_embed_one(text: str) -> list[float]:
    base = _ollama_base_url()
    payload = {"model": EMBED_MODEL, "input": text}
    with httpx.Client(timeout=EMBED_TIMEOUT_SEC) as client:
        resp = client.post(f"{base}/api/embed", json=payload)
        if resp.status_code == 404:
            resp = client.post(f"{base}/api/embeddings", json={"model": EMBED_MODEL, "prompt": text})
        resp.raise_for_status()
        data = resp.json()
    if isinstance(data.get("embeddings"), list) and data["embeddings"]:
        return [float(x) for x in data["embeddings"][0]]
    if isinstance(data.get("embedding"), list):
        return [float(x) for x in data["embedding"]]
    raise RuntimeError("Ollama embedding response missing embedding vector")


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


def _load_embedding_index(skills: list[SkillDoc]) -> dict[str, Any] | None:
    if not EMBED_INDEX_PATH.is_file():
        return None
    try:
        data = json.loads(EMBED_INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if data.get("model") != EMBED_MODEL:
        return None
    if data.get("signature") != _skill_signature(skills):
        return None
    vectors = data.get("vectors")
    if not isinstance(vectors, dict):
        return None
    return data


def _build_embedding_index(skills: list[SkillDoc]) -> dict[str, Any]:
    vectors: dict[str, list[float]] = {}
    for sk in skills:
        if sk.stem == "learned_habit_auto":
            continue
        vectors[sk.stem] = _ollama_embed_one(_skill_embedding_text(sk))
    data = {
        "model": EMBED_MODEL,
        "ollama_base": _ollama_base_url(),
        "signature": _skill_signature(skills),
        "created_at": int(time.time()),
        "vectors": vectors,
    }
    try:
        EMBED_INDEX_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return data


def _embedding_route_skills(user_message: str, skills: list[SkillDoc]) -> list[tuple[float, SkillDoc]]:
    global _EMBED_FAILURE_UNTIL
    if os.environ.get("SKILL_EMBED_ROUTER", "1").strip().lower() in {
        "0",
        "false",
        "off",
    }:
        return []
    if time.time() < _EMBED_FAILURE_UNTIL:
        return []
    try:
        with _EMBED_CACHE_LOCK:
            index = _load_embedding_index(skills)
            if index is None:
                index = _build_embedding_index(skills)
        query_vec = _ollama_embed_one(user_message)
        vectors = index.get("vectors", {})
        by_stem = {sk.stem: sk for sk in skills}
        scored: list[tuple[float, SkillDoc]] = []
        for stem, vec in vectors.items():
            sk = by_stem.get(stem)
            if sk and isinstance(vec, list):
                score = _cosine(query_vec, [float(x) for x in vec])
                if score > 0:
                    scored.append((score, sk))
        scored.sort(key=lambda x: (-x[0], x[1].title))
        return scored
    except Exception:
        _EMBED_FAILURE_UNTIL = time.time() + 300
        return []


def _skill_body_limit(top_score: int) -> int:
    if top_score >= 6:
        return 3000
    if top_score >= 4:
        return 2600
    if top_score >= 2:
        return 2200
    return 1800


def build_skill_pack_context(user_message: str) -> str:
    if not get_runtime().agent_skill_pack:
        return ""
    skills = _load_all_skills()
    if not skills:
        return ""
    forced_stem, user_message = _forced_skill_stem(user_message or "")
    if forced_stem:
        sk = next((s for s in skills if s.stem == forced_stem), None)
        if sk:
            body = sk.body[:2800] + ("…" if len(sk.body) > 2800 else "")
            trig = ", ".join(sk.triggers[:8])
            return f"## 技能包（用户指定: {sk.title} · id=`{sk.stem}`）\n命中触发: {trig}\n\n### {sk.title}\n{body}"
    semantic_scored = _embedding_route_skills(user_message or "", skills)
    text = (user_message or "").lower()
    tokens = _message_tokens(text)
    keyword_ranked: list[tuple[int, SkillDoc]] = []
    for sk in skills:
        if sk.stem == "learned_habit_auto":
            continue
        score = _score_skill(sk, text, tokens)
        if score:
            keyword_ranked.append((score, sk))
    keyword_ranked.sort(key=lambda x: (-x[0], x[1].title))
    if semantic_scored:
        merged: dict[str, tuple[float, SkillDoc]] = {}
        for score, sk in semantic_scored[:12]:
            merged[sk.stem] = (score, sk)
        # Exact trigger/keyword hits are stronger evidence than embedding similarity.
        # Keep them in the candidate set so semantic routing cannot hide obvious tools.
        for kw_score, sk in keyword_ranked[:8]:
            semantic_equivalent = 1.0 + min(0.25, kw_score * 0.03)
            old = merged.get(sk.stem)
            if old is None or semantic_equivalent > old[0]:
                merged[sk.stem] = (semantic_equivalent, sk)
        scored = sorted(merged.values(), key=lambda x: (-x[0], x[1].title))
        top_score = 6 if scored and scored[0][0] >= 0.35 else 2
    else:
        scored: list[tuple[int | float, SkillDoc]] = keyword_ranked
        top_score = int(scored[0][0]) if scored else 0
    if top_score >= 6:
        limit = 5
    elif top_score >= 4:
        limit = 4
    elif top_score >= 2:
        limit = 3
    else:
        limit = 2
    picked = [d for _, d in scored[:limit]]
    if not picked:
        for stem in (
            "persistent_context",
            "skills_master_index",
            "tool_skill_authoring",
            "spec_minimal_steps",
            "github_trending_developers",
            "weekly_trend_map",
            "trend_playbook_snapshot",
        ):
            sk = next((s for s in skills if s.stem == stem), None)
            if sk:
                picked = [sk]
                break
        else:
            picked = skills[:1]
    body_limit = _skill_body_limit(top_score)
    blocks = ["## 技能包（按任务关键词自动挂载；优先遵循「何时使用」与「执行步骤」）"]
    for sk in picked:
        body = sk.body
        if len(body) > body_limit:
            body = body[:body_limit] + "\n…"
        trig = ", ".join(sk.triggers[:6])
        blocks.append(f"### {sk.title} (`{sk.stem}`)\n触发: {trig}\n\n{body}")
    return "\n\n".join(blocks)
