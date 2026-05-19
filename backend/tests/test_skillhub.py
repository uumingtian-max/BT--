import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from skillhub import (  # noqa: E402
    _parse_frontmatter,
    _parse_simple_yaml,
    audit_skillhub,
    get_skillhub_record,
    list_skillhub_records,
    skillhub_summary,
)


def test_parse_simple_yaml_frontmatter_subset():
    meta = _parse_simple_yaml(
        """
name: demo-skill
description: Demo skill
version: 1.0.0
platforms: [windows, linux]
metadata:
  hermes:
    tags: [demo, test]
""".strip()
    )
    assert meta["name"] == "demo-skill"
    assert meta["platforms"] == ["windows", "linux"]
    assert meta["metadata"]["hermes"]["tags"] == ["demo", "test"]


def test_parse_frontmatter_returns_body():
    meta, body = _parse_frontmatter("---\nname: demo\n---\n# Demo\nBody")
    assert meta["name"] == "demo"
    assert "# Demo" in body


def test_skillhub_lists_existing_core_skills():
    records = list_skillhub_records()
    assert records
    assert any(item.source == "core" for item in records)
    assert any(item.name == "skills-master-index" for item in records)


def test_skillhub_summary_counts_sources_and_risks():
    summary = skillhub_summary()
    assert summary["ok"] is True
    assert summary["count"] >= 1
    assert summary["sources"]["core"] >= 1
    assert set(summary["risks"]).issuperset({"safe", "confirm", "dangerous"})


def test_skillhub_detail_lookup_by_id_or_name():
    record = get_skillhub_record("skills-master-index")
    assert record is not None
    assert record.source == "core"
    assert record.to_dict(include_content=True)["content"]


def test_skillhub_audit_shape():
    audit = audit_skillhub()
    assert "ok" in audit
    assert "findings" in audit
    assert isinstance(audit["findings"], list)
