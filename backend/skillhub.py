"""BKLT SkillHub registry and safety audit core.

SkillHub v1 is intentionally read-only: it indexes core, optional, user, and
quarantined skills, then reports metadata and static risk signals. Installing or
executing external skills is handled in later phases after stronger policy gates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
CORE_SKILLS_DIR = BACKEND_DIR / "agent_skills"
OPTIONAL_SKILLS_DIR = BACKEND_DIR / "optional_skills"
USER_SKILLS_DIR = BACKEND_DIR / "user_skills"
QUARANTINE_DIR = BACKEND_DIR / "skill_quarantine"

SKILL_SOURCE_DIRS: tuple[tuple[str, Path, str], ...] = (
    ("core", CORE_SKILLS_DIR, "builtin"),
    ("optional", OPTIONAL_SKILLS_DIR, "official"),
    ("user", USER_SKILLS_DIR, "user"),
    ("quarantine", QUARANTINE_DIR, "quarantine"),
)

RISK_LEVELS = {"safe", "confirm", "dangerous"}

DANGEROUS_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("dangerous_delete", r"\brm\s+-rf\b|\bdel\s+/[fsq]\b|\brmdir\s+/s\b", "dangerous"),
    ("disk_format", r"\bformat\s+[a-z]:|clear-disk|remove-partition", "dangerous"),
    ("secret_exfiltration", r"exfiltrat|上传.*(token|key|secret)|send.*(token|key|secret)", "dangerous"),
    ("private_key_access", r"id_rsa|BEGIN\s+(RSA|OPENSSH|PRIVATE)\s+KEY", "dangerous"),
    ("env_secret_access", r"OPENAI_API_KEY|API_KEY|SECRET|PASSWORD|TOKEN", "confirm"),
    ("network_download", r"Invoke-WebRequest|curl\s+|wget\s+|irm\s+|iwr\s+", "confirm"),
    ("process_spawn", r"subprocess|Start-Process|os\.system|exec\(|eval\(", "confirm"),
    ("shell_script", r"\.ps1\b|\.bat\b|\.sh\b|powershell|cmd\.exe|bash\b", "confirm"),
)

_SAFE_TEXT_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml"}
_SCRIPT_EXTENSIONS = {".py", ".ps1", ".bat", ".cmd", ".sh", ".js", ".ts"}


@dataclass(frozen=True)
class SkillRecord:
    id: str
    name: str
    title: str
    description: str
    source: str
    trust_level: str
    category: str
    path: str
    relative_path: str
    enabled: bool
    risk_level: str
    risk_signals: tuple[dict[str, str], ...]
    tags: tuple[str, ...]
    platforms: tuple[str, ...]
    version: str
    has_references: bool
    has_scripts: bool

    def to_dict(self, *, include_content: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "trust_level": self.trust_level,
            "category": self.category,
            "path": self.path,
            "relative_path": self.relative_path,
            "enabled": self.enabled,
            "risk_level": self.risk_level,
            "risk_signals": list(self.risk_signals),
            "tags": list(self.tags),
            "platforms": list(self.platforms),
            "version": self.version,
            "has_references": self.has_references,
            "has_scripts": self.has_scripts,
        }
        if include_content:
            data["content"] = _read_text(Path(self.path))
        return data


def ensure_skillhub_dirs() -> None:
    """Create local SkillHub directories when the app starts or registry is read."""
    for _, directory, _ in SKILL_SOURCE_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def list_skillhub_records() -> list[SkillRecord]:
    ensure_skillhub_dirs()
    records: list[SkillRecord] = []
    for source, directory, trust_level in SKILL_SOURCE_DIRS:
        records.extend(_scan_skill_dir(source=source, directory=directory, trust_level=trust_level))
    return sorted(records, key=lambda item: (item.source, item.category, item.name))


def get_skillhub_record(skill_id: str) -> SkillRecord | None:
    normalized = _slug(skill_id)
    for record in list_skillhub_records():
        if record.id == normalized or record.name == normalized:
            return record
    return None


def skillhub_summary() -> dict[str, Any]:
    records = list_skillhub_records()
    by_source: dict[str, int] = {}
    by_risk: dict[str, int] = {"safe": 0, "confirm": 0, "dangerous": 0}
    for record in records:
        by_source[record.source] = by_source.get(record.source, 0) + 1
        by_risk[record.risk_level] = by_risk.get(record.risk_level, 0) + 1
    return {
        "ok": True,
        "count": len(records),
        "sources": by_source,
        "risks": by_risk,
        "dirs": {
            "core": str(CORE_SKILLS_DIR),
            "optional": str(OPTIONAL_SKILLS_DIR),
            "user": str(USER_SKILLS_DIR),
            "quarantine": str(QUARANTINE_DIR),
        },
    }


def audit_skillhub() -> dict[str, Any]:
    records = list_skillhub_records()
    findings: list[dict[str, Any]] = []
    for record in records:
        if record.risk_signals:
            findings.append(
                {
                    "id": record.id,
                    "name": record.name,
                    "source": record.source,
                    "risk_level": record.risk_level,
                    "signals": list(record.risk_signals),
                }
            )
    dangerous = [f for f in findings if f["risk_level"] == "dangerous"]
    confirm = [f for f in findings if f["risk_level"] == "confirm"]
    return {
        "ok": len(dangerous) == 0,
        "count": len(records),
        "findings_count": len(findings),
        "dangerous_count": len(dangerous),
        "confirm_count": len(confirm),
        "findings": findings,
    }


def _scan_skill_dir(*, source: str, directory: Path, trust_level: str) -> list[SkillRecord]:
    if not directory.exists():
        return []
    records: list[SkillRecord] = []
    for skill_file in _iter_skill_files(directory):
        record = _record_from_file(source=source, trust_level=trust_level, base_dir=directory, path=skill_file)
        if record:
            records.append(record)
    return records


def _iter_skill_files(directory: Path) -> list[Path]:
    direct_md = [p for p in directory.glob("*.md") if p.name.upper() != "DESCRIPTION.MD"]
    nested = list(directory.glob("**/SKILL.md"))
    return sorted({*direct_md, *nested})


def _record_from_file(*, source: str, trust_level: str, base_dir: Path, path: Path) -> SkillRecord | None:
    content = _read_text(path)
    if not content.strip():
        return None
    meta, body = _parse_frontmatter(content)
    rel = path.relative_to(base_dir).as_posix()
    category = _category_from_path(source=source, rel=rel)
    name = _slug(str(meta.get("name") or path.parent.name if path.name == "SKILL.md" else path.stem))
    title = str(meta.get("title") or _extract_heading(body) or name).strip()
    description = str(meta.get("description") or _extract_description(body) or "").strip()
    tags = tuple(
        _as_list(_nested_get(meta, ("metadata", "bklt", "tags")) or _nested_get(meta, ("metadata", "hermes", "tags")))
    )
    platforms = tuple(_as_list(meta.get("platforms")))
    version = str(meta.get("version") or "").strip()
    has_references = (path.parent / "references").is_dir()
    has_scripts = (path.parent / "scripts").is_dir() or any(
        p.suffix.lower() in _SCRIPT_EXTENSIONS for p in path.parent.glob("scripts/*")
    )
    risk_signals, risk_level = _audit_content(content=content, skill_dir=path.parent, source=source)
    enabled = source in {"core", "user"} and risk_level != "dangerous"
    skill_id = _slug(f"{source}-{category}-{name}")
    return SkillRecord(
        id=skill_id,
        name=name,
        title=title,
        description=description,
        source=source,
        trust_level=trust_level,
        category=category,
        path=str(path),
        relative_path=str(path.relative_to(ROOT).as_posix()),
        enabled=enabled,
        risk_level=risk_level,
        risk_signals=tuple(risk_signals),
        tags=tags,
        platforms=platforms,
        version=version,
        has_references=has_references,
        has_scripts=has_scripts,
    )


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---", 4)
    if end == -1:
        return {}, content
    raw = content[4:end].strip()
    body = content[end + 4 :]
    return _parse_simple_yaml(raw), body


def _parse_simple_yaml(raw: str) -> dict[str, Any]:
    """Small YAML-ish parser for skill metadata; avoids requiring PyYAML."""
    out: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, out)]
    lines = raw.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if stripped.startswith("-") or ":" not in stripped:
            index += 1
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value in {"", "|", ">"}:
            if value in {"|", ">"}:
                block_lines: list[str] = []
                block_indent = None
                j = index + 1
                while j < len(lines):
                    nxt = lines[j]
                    if not nxt.strip():
                        block_lines.append("")
                        j += 1
                        continue
                    nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                    if nxt_indent <= indent:
                        break
                    if block_indent is None:
                        block_indent = nxt_indent
                    block_lines.append(nxt[block_indent:])
                    j += 1
                parent[key] = "\n".join(block_lines).strip()
                index = j
                continue
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value)
        index += 1
    return out


def _parse_scalar(value: str) -> Any:
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
    return value.strip().strip("'\"")


def _nested_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _as_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("[") and raw.endswith("]"):
            raw = raw[1:-1]
        return [x.strip().strip("'\"") for x in raw.split(",") if x.strip()]
    return [str(value).strip()]


def _extract_heading(body: str) -> str:
    match = re.search(r"^#\s+(.+)$", body, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_description(body: str) -> str:
    for paragraph in re.split(r"\n\s*\n", body):
        text = paragraph.strip()
        if not text or text.startswith("#") or text.lower().startswith("triggers:") or text == "---":
            continue
        return re.sub(r"\s+", " ", text)[:280]
    return ""


def _category_from_path(*, source: str, rel: str) -> str:
    parts = rel.split("/")
    if source == "core":
        stem = Path(rel).stem
        if stem.startswith("tool_"):
            return "tools"
        if stem.startswith("feature_"):
            return "features"
        if stem.startswith(("onyx_", "bklt_", "bt_")):
            return "bklt"
        if stem.startswith("learned_"):
            return "learned"
        return "core"
    return _slug(parts[0]) if len(parts) > 1 else source


def _audit_content(*, content: str, skill_dir: Path, source: str) -> tuple[list[dict[str, str]], str]:
    signals: list[dict[str, str]] = []
    risk = "safe"
    for code, pattern, level in DANGEROUS_PATTERNS:
        if re.search(pattern, content, flags=re.IGNORECASE):
            signals.append({"code": code, "level": level})
            risk = _max_risk(risk, level)
    if source == "quarantine":
        signals.append({"code": "quarantined_source", "level": "confirm"})
        risk = _max_risk(risk, "confirm")
    if (skill_dir / "scripts").is_dir():
        script_files = [p for p in (skill_dir / "scripts").glob("**/*") if p.is_file()]
        if script_files:
            signals.append({"code": "bundled_scripts", "level": "confirm"})
            risk = _max_risk(risk, "confirm")
            for script in script_files[:12]:
                if script.suffix.lower() not in _SAFE_TEXT_EXTENSIONS:
                    script_text = _read_text(script)
                    for code, pattern, level in DANGEROUS_PATTERNS:
                        if re.search(pattern, script_text, flags=re.IGNORECASE):
                            signals.append({"code": f"script:{code}", "level": level})
                            risk = _max_risk(risk, level)
    return _dedupe_signals(signals), risk


def _dedupe_signals(signals: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for item in signals:
        key = (item["code"], item["level"])
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _max_risk(a: str, b: str) -> str:
    rank = {"safe": 0, "confirm": 1, "dangerous": 2}
    return a if rank.get(a, 0) >= rank.get(b, 0) else b


def _slug(value: str) -> str:
    value = value.strip().lower().replace(" ", "-").replace("_", "-")
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "skill"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
