"""Tests for monetize-27 expert routing."""

from __future__ import annotations

import expert_roles as er


def test_monetize_count():
    m = er.get_expert_roles_manifest()
    assert m["counts"]["monetize_experts"] == 27
    assert m["counts"]["total_roles"] == 39  # boss + 11 core + 27


def test_route_ecommerce():
    ids = er.monetize_expert_ids_for_task("帮我优化淘宝店铺转化和定价")
    assert "ecommerce_ops" in ids


def test_route_automation_fallback():
    ids = er.monetize_expert_ids_for_task("我想赚钱自动化")
    assert "revenue_architect" in ids


def test_monetize_disabled(monkeypatch):
    monkeypatch.setenv("BKLT_MONETIZE_27", "0")
    assert er.monetize_expert_ids_for_task("电商带货") == []
