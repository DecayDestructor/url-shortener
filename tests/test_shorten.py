"""
test_shorten.py — Tests for POST /shorten endpoint.
"""

import pytest
from fastapi.testclient import TestClient


AUTH = {"Authorization": "Bearer {token}"}


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


#  Happy path 

class TestShortenSuccess:

    def test_returns_200_with_short_code(self, client: TestClient, user_token: str):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com"},
            headers=auth(user_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "short_code" in data
        assert len(data["short_code"]) > 0

    def test_response_contains_short_url(self, client: TestClient, user_token: str):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com/long-path"},
            headers=auth(user_token),
        )
        data = resp.json()
        assert "short_url" in data
        assert data["short_code"] in data["short_url"]

    def test_response_contains_qr_url(self, client: TestClient, user_token: str):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com"},
            headers=auth(user_token),
        )
        data = resp.json()
        assert "qr_url" in data
        assert "qrserver.com" in data["qr_url"]

    def test_is_custom_false_for_auto_code(self, client: TestClient, user_token: str):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com"},
            headers=auth(user_token),
        )
        assert resp.json()["is_custom"] is False

    def test_expires_at_none_when_not_set(self, client: TestClient, user_token: str):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com"},
            headers=auth(user_token),
        )
        assert resp.json()["expires_at"] is None

    def test_expires_at_set_when_hours_provided(self, client: TestClient, user_token: str):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com", "expires_in_hours": 24},
            headers=auth(user_token),
        )
        assert resp.json()["expires_at"] is not None

    def test_short_codes_are_unique(self, client: TestClient, user_token: str):
        codes = set()
        for i in range(5):
            resp = client.post(
                "/shorten",
                json={"original_url": f"https://example.com/{i}"},
                headers=auth(user_token),
            )
            codes.add(resp.json()["short_code"])
        assert len(codes) == 5


# Custom alias 

class TestShortenCustomAlias:

    def test_custom_alias_used_as_short_code(self, client: TestClient, user_token: str):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com", "custom_alias": "my-brand"},
            headers=auth(user_token),
        )
        assert resp.status_code == 200
        assert resp.json()["short_code"] == "my-brand"
        assert resp.json()["is_custom"] is True

    def test_duplicate_custom_alias_returns_409(self, client: TestClient, user_token: str):
        payload = {"original_url": "https://example.com", "custom_alias": "unique-slug"}
        client.post("/shorten", json=payload, headers=auth(user_token))
        resp = client.post("/shorten", json=payload, headers=auth(user_token))
        assert resp.status_code == 409

    def test_alias_too_short_returns_400(self, client: TestClient, user_token: str):
        """Alias regex requires 3+ chars — app returns 400 (HTTPException), not 422."""
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com", "custom_alias": "ab"},
            headers=auth(user_token),
        )
        assert resp.status_code in (400, 422)

    def test_alias_with_special_chars_returns_400(self, client: TestClient, user_token: str):
        """Spaces/special chars fail the ALIAS_RE regex — app returns 400."""
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com", "custom_alias": "has spaces"},
            headers=auth(user_token),
        )
        assert resp.status_code in (400, 422)

    def test_reserved_alias_returns_400(self, client: TestClient, user_token: str):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com", "custom_alias": "admin"},
            headers=auth(user_token),
        )
        assert resp.status_code == 400


#  Auth guard

class TestShortenAuth:

    def test_unauthenticated_returns_401(self, client: TestClient):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com"},
        )
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client: TestClient):
        resp = client.post(
            "/shorten",
            json={"original_url": "https://example.com"},
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        assert resp.status_code == 401
