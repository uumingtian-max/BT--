from __future__ import annotations

from fastapi.testclient import TestClient


def test_mobile_auth_status_local_not_required(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("MOBILE_ACCESS_TOKEN", "secret")
    r = client.get("/mobile-auth/status", headers={"host": "127.0.0.1:8002"})
    assert r.status_code == 200
    assert r.json()["required"] is False


def test_mobile_auth_status_tailscale_not_required(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("MOBILE_ACCESS_TOKEN", "secret")
    r = client.get("/mobile-auth/status", headers={"host": "100.114.73.101:8002"})
    assert r.status_code == 200
    assert r.json()["required"] is False


def test_mobile_auth_blocks_public_api(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("MOBILE_ACCESS_TOKEN", "secret")
    r = client.get("/meta/doctor", headers={"host": "agent.example.com"})
    assert r.status_code == 401
    assert r.json()["auth_required"] is True


def test_mobile_auth_login_cookie_allows_public_api(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("MOBILE_ACCESS_TOKEN", "secret")
    login = client.post("/mobile-auth/login", json={"token": "secret"}, headers={"host": "agent.example.com"})
    assert login.status_code == 200
    r = client.get("/meta/doctor", headers={"host": "agent.example.com"})
    assert r.status_code == 200
