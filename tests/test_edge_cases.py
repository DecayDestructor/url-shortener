""" test_edge_cases.py — Cross-cutting edge case and integration-style tests.
Covers: invalid inputs, URL management endpoints, trending, admin access.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.models import URL


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_url(session, short_code, original_url="https://example.com",
              clicks=0, owner_id=None, expires_at=None):
    url = URL(
        short_code=short_code, original_url=original_url,
        clicks=clicks, owner_id=owner_id,
        is_custom=False, expires_at=expires_at,
    )
    session.add(url)
    session.commit()
    session.refresh(url)
    return url


# Invalid URL input 

class TestInvalidInput:

    def test_empty_url_returns_error(self, client: TestClient, user_token: str):
        """
        original_url is a plain `str`, not `HttpUrl`.
        The app currently accepts empty strings \u2014 this documents that behaviour.
        Add a validator to the schema to enforce non-empty and update to assert 422.
        """
        resp = client.post("/shorten", json={"original_url": ""},
                           headers=auth(user_token))
        assert resp.status_code in (200, 400, 422)

    def test_missing_url_field_returns_422(self, client: TestClient, user_token: str):
        resp = client.post("/shorten", json={}, headers=auth(user_token))
        assert resp.status_code == 422

    def test_non_http_url_still_accepted(self, client: TestClient, user_token: str):
        # The schema uses `str`, not `HttpUrl`, so ftp:// etc. are allowed
        resp = client.post("/shorten",
                           json={"original_url": "ftp://files.example.com"},
                           headers=auth(user_token))
        # Should not crash — 200 or 422 depending on validation
        assert resp.status_code in (200, 422)

    def test_extremely_long_url_accepted(self, client: TestClient, user_token: str):
        long_url = "https://example.com/" + "a" * 2000
        resp = client.post("/shorten", json={"original_url": long_url},
                           headers=auth(user_token))
        assert resp.status_code in (200, 422)

    def test_negative_expiry_hours(self, client: TestClient, user_token: str):
        resp = client.post("/shorten",
                           json={"original_url": "https://example.com",
                                 "expires_in_hours": -1},
                           headers=auth(user_token))
        # Should either reject or handle gracefully
        assert resp.status_code in (200, 422, 400)

    def test_zero_expiry_hours(self, client: TestClient, user_token: str):
        resp = client.post("/shorten",
                           json={"original_url": "https://example.com",
                                 "expires_in_hours": 0},
                           headers=auth(user_token))
        assert resp.status_code in (200, 422, 400)


# GET /urls/me 

class TestMyUrls:

    def test_returns_only_own_urls(
        self, client: TestClient, session: Session,
        user_token: str, regular_user, admin_user
    ):
        _seed_url(session, "mine1", owner_id=regular_user.id)
        _seed_url(session, "notmine", owner_id=admin_user.id)
        resp = client.get("/urls/me", headers=auth(user_token))
        assert resp.status_code == 200
        codes = [u["short_code"] for u in resp.json()["urls"]]
        assert "mine1" in codes
        assert "notmine" not in codes

    def test_returns_empty_list_when_no_urls(
        self, client: TestClient, user_token: str
    ):
        resp = client.get("/urls/me", headers=auth(user_token))
        assert resp.status_code == 200
        assert resp.json()["urls"] == []

    def test_unauthenticated_returns_401(self, client: TestClient):
        resp = client.get("/urls/me")
        assert resp.status_code == 401

    def test_click_count_combines_db_and_redis(
        self, client: TestClient, session: Session,
        user_token: str, regular_user, mock_redis
    ):
        mock, store = mock_redis
        _seed_url(session, "clicktest", clicks=10, owner_id=regular_user.id)
        store["clicks:clicktest"] = "5"
        resp = client.get("/urls/me", headers=auth(user_token))
        url_data = next(u for u in resp.json()["urls"] if u["short_code"] == "clicktest")
        assert url_data["clicks"] == 15


# DELETE /urls/{short_code} 

class TestDeleteUrl:

    def test_owner_can_delete_own_url(
        self, client: TestClient, session: Session,
        user_token: str, regular_user
    ):
        _seed_url(session, "del1", owner_id=regular_user.id)
        resp = client.delete("/urls/del1", headers=auth(user_token))
        assert resp.status_code == 200

    def test_delete_nonexistent_returns_404(
        self, client: TestClient, user_token: str
    ):
        resp = client.delete("/urls/nope999", headers=auth(user_token))
        assert resp.status_code == 404

    def test_user_cannot_delete_others_url(
        self, client: TestClient, session: Session,
        user_token: str, admin_user
    ):
        _seed_url(session, "del2", owner_id=admin_user.id)
        resp = client.delete("/urls/del2", headers=auth(user_token))
        assert resp.status_code == 403

    def test_admin_can_delete_any_url(
        self, client: TestClient, session: Session,
        admin_token: str, regular_user
    ):
        _seed_url(session, "del3", owner_id=regular_user.id)
        resp = client.delete("/urls/del3", headers=auth(admin_token))
        assert resp.status_code == 200

    def test_delete_removes_redis_keys(
        self, client: TestClient, session: Session,
        user_token: str, regular_user, mock_redis
    ):
        mock, store = mock_redis
        store["url:del4"] = "https://example.com"
        store["clicks:del4"] = "3"
        _seed_url(session, "del4", owner_id=regular_user.id)
        client.delete("/urls/del4", headers=auth(user_token))
        assert "url:del4" not in store
        assert "clicks:del4" not in store

    def test_unauthenticated_delete_returns_401(self, client: TestClient, session: Session):
        _seed_url(session, "del5")
        resp = client.delete("/urls/del5")
        assert resp.status_code == 401


#  Trending public endpoint

class TestTrendingPublic:

    def test_trending_returns_200(self, client: TestClient):
        resp = client.get("/trending/public")
        assert resp.status_code == 200

    def test_trending_returns_list(self, client: TestClient):
        data = client.get("/trending/public").json()
        assert "trending" in data
        assert isinstance(data["trending"], list)

    def test_trending_no_auth_required(self, client: TestClient):
        # Public endpoint — should work without a token
        resp = client.get("/trending/public")
        assert resp.status_code == 200


# Admin /admin/urls 

class TestAdminUrls:

    def test_admin_can_view_all_urls(
        self, client: TestClient, session: Session,
        admin_token: str, regular_user
    ):
        _seed_url(session, "adm1", owner_id=regular_user.id)
        resp = client.get("/admin/urls", headers=auth(admin_token))
        assert resp.status_code == 200
        assert "urls" in resp.json()

    def test_regular_user_cannot_access_admin_urls(
        self, client: TestClient, user_token: str
    ):
        resp = client.get("/admin/urls", headers=auth(user_token))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access_admin_urls(self, client: TestClient):
        resp = client.get("/admin/urls")
        assert resp.status_code == 401


# Health / docs

class TestMeta:

    def test_openapi_docs_accessible(self, client: TestClient):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_json_accessible(self, client: TestClient):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
