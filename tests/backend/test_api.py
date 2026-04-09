import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add backend to path so `app` package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_register_user():
    resp = client.post("/api/auth/register", json={
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "securepassword123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser1"


def test_register_duplicate_username():
    client.post("/api/auth/register", json={
        "username": "dupeuser",
        "email": "dupe1@example.com",
        "password": "password123",
    })
    resp = client.post("/api/auth/register", json={
        "username": "dupeuser",
        "email": "dupe2@example.com",
        "password": "password123",
    })
    assert resp.status_code == 400


def test_login_success():
    client.post("/api/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "password123",
    })
    resp = client.post("/api/auth/login", data={
        "username": "loginuser",
        "password": "password123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password():
    client.post("/api/auth/register", json={
        "username": "wrongpw",
        "email": "wrongpw@example.com",
        "password": "password123",
    })
    resp = client.post("/api/auth/login", data={
        "username": "wrongpw",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_me_authenticated():
    client.post("/api/auth/register", json={
        "username": "meuser",
        "email": "me@example.com",
        "password": "password123",
    })
    login = client.post("/api/auth/login", data={
        "username": "meuser",
        "password": "password123",
    })
    token = login.json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "meuser"


def test_me_unauthenticated():
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_orchestrator_requires_auth():
    resp = client.post("/api/orchestrator/run", json={"message": "hello"})
    assert resp.status_code == 401


def test_orchestrator_with_auth():
    client.post("/api/auth/register", json={
        "username": "orchuser",
        "email": "orch@example.com",
        "password": "password123",
    })
    login = client.post("/api/auth/login", data={
        "username": "orchuser",
        "password": "password123",
    })
    token = login.json()["access_token"]
    resp = client.post(
        "/api/orchestrator/run",
        json={"message": "Create a support ticket"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "reply" in resp.json()
