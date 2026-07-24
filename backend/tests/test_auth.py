"""Tests for authentication endpoints using FastAPI TestClient with dependency override."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
from app.models import Constellation, OrganizationMembership
from app.core.database import get_db

# ── In-memory test database ──────────────────────────────────────────────────
# StaticPool + check_same_thread=False required for SQLite with FastAPI TestClient.

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(test_engine)
TestSessionLocal = sessionmaker(bind=test_engine)


def get_test_db():
    """FastAPI dependency override: yields an in-memory SQLite session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _setup_test_db():
    """Recreate tables before each test and patch the DB dependency."""
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    app.dependency_overrides[get_db] = get_test_db
    yield
    app.dependency_overrides.clear()


# ── Client ───────────────────────────────────────────────────────────────────

client = TestClient(app)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestRegister:
    def test_register_success(self):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "longpassword123",
                "name": "Test User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["plan"] == "free"
        with TestSessionLocal() as db:
            membership = (
                db.query(OrganizationMembership)
                .filter(OrganizationMembership.user_id == uuid.UUID(data["id"]))
                .one()
            )
            assert membership.role == "owner"
            assert (
                db.query(Constellation)
                .filter(Constellation.organization_id == membership.organization_id)
                .count()
                == 1
            )

    def test_register_duplicate_email(self):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "longpassword123",
            },
        )
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "longpassword123",
            },
        )
        assert resp.status_code == 409

    def test_register_short_password(self):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
            },
        )
        assert resp.status_code == 422

    def test_register_invalid_email(self):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "longpassword123",
            },
        )
        assert resp.status_code == 422


class TestLogin:
    def _create_user(self, email="test@example.com", password="longpassword123"):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_login_success(self):
        self._create_user()
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "longpassword123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "test@example.com"

    def test_login_wrong_password(self):
        self._create_user()
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self):
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "longpassword123",
            },
        )
        assert resp.status_code == 401


class TestMe:
    def test_me_with_valid_token(self):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "longpassword123",
            },
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "longpassword123",
            },
        )
        token = login_resp.json()["access_token"]

        resp = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_me_with_invalid_token(self):
        resp = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken123"}
        )
        assert resp.status_code == 401

    def test_me_without_token(self):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
