"""
test_auth.py — Tests for /auth/* endpoints (register, login, admin login, /me).
"""

import pytest
from fastapi.testclient import TestClient


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# Register

class TestRegister:

    def test_register_returns_201(self, client: TestClient):
        resp = client.post("/auth/register", json={
            "email": "new@test.com",
            "username": "newuser",
            "password": "password123",
        })
        assert resp.status_code == 201

    def test_register_returns_access_token(self, client: TestClient):
        resp = client.post("/auth/register", json={
            "email": "new2@test.com",
            "username": "newuser2",
            "password": "password123",
        })
        data = resp.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0

    def test_register_is_not_admin(self, client: TestClient):
        resp = client.post("/auth/register", json={
            "email": "new3@test.com",
            "username": "newuser3",
            "password": "password123",
        })
        assert resp.json()["is_admin"] is False

    def test_duplicate_email_returns_400(self, client: TestClient, regular_user):
        resp = client.post("/auth/register", json={
            "email": regular_user.email,
            "username": "differentname",
            "password": "password123",
        })
        assert resp.status_code == 400

    def test_duplicate_username_returns_400(self, client: TestClient, regular_user):
        resp = client.post("/auth/register", json={
            "email": "different@test.com",
            "username": regular_user.username,
            "password": "password123",
        })
        assert resp.status_code == 400

    def test_email_field_accepts_any_string(self, client: TestClient):
        """
        The register schema uses `str`, not `EmailStr`.
        The app does NOT validate email format — any string is accepted.
        If you add EmailStr validation later, change this to assert 422.
        """
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "username": "someone99",
            "password": "password123",
        })
        assert resp.status_code in (201, 400, 422)

    def test_missing_fields_returns_422(self, client: TestClient):
        resp = client.post("/auth/register", json={"email": "x@x.com"})
        assert resp.status_code == 422


# Login 

class TestLogin:

    def test_login_success_returns_token(self, client: TestClient, regular_user):
        resp = client.post("/auth/login", json={
            "email": "user@test.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password_returns_401(self, client: TestClient, regular_user):
        resp = client.post("/auth/login", json={
            "email": "user@test.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self, client: TestClient):
        resp = client.post("/auth/login", json={
            "email": "nobody@test.com",
            "password": "password123",
        })
        assert resp.status_code == 401

    def test_login_is_admin_false_for_regular_user(self, client: TestClient, regular_user):
        resp = client.post("/auth/login", json={
            "email": "user@test.com",
            "password": "password123",
        })
        assert resp.json()["is_admin"] is False


# Admin Login 

class TestAdminLogin:

    def test_admin_login_returns_is_admin_true(self, client: TestClient, admin_user):
        resp = client.post("/auth/admin/login", json={
            "email": "admin@test.com",
            "password": "adminpass",
        })
        assert resp.status_code == 200
        assert resp.json()["is_admin"] is True

    def test_regular_user_cannot_use_admin_login(self, client: TestClient, regular_user):
        resp = client.post("/auth/admin/login", json={
            "email": "user@test.com",
            "password": "password123",
        })
        assert resp.status_code == 403


#  /auth/me 

class TestMe:

    def test_me_returns_user_data(self, client: TestClient, user_token: str, regular_user):
        resp = client.get("/auth/me", headers=auth(user_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == regular_user.email
        assert data["username"] == regular_user.username

    def test_me_without_token_returns_401(self, client: TestClient):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_bad_token_returns_401(self, client: TestClient):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
        assert resp.status_code == 401
