""" test_redirect.py — Tests for GET /{short_code} (redirect endpoint).
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.models import URL


def _seed_url(
    session: Session,
    short_code: str = "testcode",
    original_url: str = "https://destination.com",
    expires_at=None,
    owner_id: int = None,
) -> URL:
    url = URL(
        short_code=short_code,
        original_url=original_url,
        clicks=0,
        owner_id=owner_id,
        is_custom=False,
        expires_at=expires_at,
    )
    session.add(url)
    session.commit()
    session.refresh(url)
    return url


# Happy path 

class TestRedirectSuccess:

    def test_redirect_returns_3xx(self, client: TestClient, session: Session):
        _seed_url(session, short_code="redir1", original_url="https://example.com")
        resp = client.get("/redir1", follow_redirects=False)
        assert resp.status_code in (301, 302, 307, 308)

    def test_redirect_location_header_matches_original(
        self, client: TestClient, session: Session
    ):
        _seed_url(session, short_code="redir2", original_url="https://target.example.com")
        resp = client.get("/redir2", follow_redirects=False)
        assert resp.headers["location"] == "https://target.example.com"

    def test_redirect_increments_click_count_in_redis(
        self, client: TestClient, session: Session, mock_redis
    ):
        mock, store = mock_redis
        _seed_url(session, short_code="redir3", original_url="https://example.com")
        client.get("/redir3", follow_redirects=False)
        # clicks counter should have been incremented
        assert store.get("clicks:redir3") is not None

    def test_redirect_adds_to_trending(
        self, client: TestClient, session: Session, mock_redis
    ):
        mock, store = mock_redis
        _seed_url(session, short_code="redir4", original_url="https://example.com")
        client.get("/redir4", follow_redirects=False)
        mock.zincrby.assert_called()

    def test_redirect_caches_url_in_redis(
        self, client: TestClient, session: Session, mock_redis
    ):
        mock, store = mock_redis
        # Empty cache first
        store.pop("url:redir5", None)
        _seed_url(session, short_code="redir5", original_url="https://cached.example.com")
        client.get("/redir5", follow_redirects=False)
        assert store.get("url:redir5") == "https://cached.example.com"

    def test_redirect_uses_cache_on_second_visit(
        self, client: TestClient, session: Session, mock_redis
    ):
        mock, store = mock_redis
        _seed_url(session, short_code="redir6", original_url="https://example.com")
        # First visit — populates cache
        client.get("/redir6", follow_redirects=False)
        get_call_count_after_first = mock.get.call_count
        # Second visit — should hit cache
        client.get("/redir6", follow_redirects=False)
        assert mock.get.call_count > get_call_count_after_first


# Edge cases 

class TestRedirectEdgeCases:

    def test_nonexistent_code_returns_404(self, client: TestClient):
        resp = client.get("/doesnotexist999", follow_redirects=False)
        assert resp.status_code == 404

    def test_expired_link_returns_410(self, client: TestClient, session: Session):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        _seed_url(
            session,
            short_code="expired1",
            original_url="https://example.com",
            expires_at=past,
        )
        resp = client.get("/expired1", follow_redirects=False)
        assert resp.status_code == 410

    def test_active_link_with_future_expiry_redirects(
        self, client: TestClient, session: Session
    ):
        future = datetime.now(timezone.utc) + timedelta(hours=24)
        _seed_url(
            session,
            short_code="notexpired",
            original_url="https://example.com",
            expires_at=future,
        )
        resp = client.get("/notexpired", follow_redirects=False)
        assert resp.status_code in (301, 302, 307, 308)

    def test_reserved_words_not_redirected(self, client: TestClient):
        # These paths should not be treated as short codes
        for reserved in ["shorten", "stats", "admin", "auth", "docs"]:
            resp = client.get(f"/{reserved}", follow_redirects=False)
            assert resp.status_code != 307, f"'{reserved}' should not redirect"
