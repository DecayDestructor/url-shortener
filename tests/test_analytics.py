"""
test_analytics.py — Tests for GET /analytics/{short_code} endpoint.

Verifies: click counts, device breakdown, referrer tracking,
          recent click activity, and access control.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.models import URL, ClickEvent


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_url(
    session: Session,
    short_code: str,
    original_url: str = "https://example.com",
    clicks: int = 0,
    owner_id: int = None,
) -> URL:
    url = URL(
        short_code=short_code,
        original_url=original_url,
        clicks=clicks,
        owner_id=owner_id,
        is_custom=False,
        expires_at=None,
    )
    session.add(url)
    session.commit()
    session.refresh(url)
    return url


def _seed_clicks(session: Session, short_code: str, events: list[dict]):
    """
    events: list of dicts with keys: device_type, referrer
    """
    for ev in events:
        click = ClickEvent(
            short_code=short_code,
            clicked_at=datetime.now(timezone.utc),
            device_type=ev.get("device_type", "desktop"),
            referrer=ev.get("referrer"),
            user_agent=None,
        )
        session.add(click)
    session.commit()


# Response structure 

class TestAnalyticsResponse:

    def test_returns_200_for_valid_code(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana1", owner_id=regular_user.id)
        resp = client.get("/analytics/ana1", headers=auth(user_token))
        assert resp.status_code == 200

    def test_response_contains_required_fields(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana2", owner_id=regular_user.id)
        data = client.get("/analytics/ana2", headers=auth(user_token)).json()
        for field in [
            "short_code", "original_url", "total_clicks",
            "created_at", "device_breakdown", "top_referrers", "recent_clicks",
        ]:
            assert field in data, f"Missing field: {field}"

    def test_total_clicks_includes_db_and_redis(
        self, client: TestClient, session: Session, user_token: str,
        regular_user, mock_redis
    ):
        mock, store = mock_redis
        _seed_url(session, "ana3", clicks=5, owner_id=regular_user.id)
        # Simulate 3 live (unsynced) Redis clicks
        store["clicks:ana3"] = "3"

        data = client.get("/analytics/ana3", headers=auth(user_token)).json()
        assert data["total_clicks"] == 8  # 5 DB + 3 Redis

    def test_total_clicks_zero_when_no_activity(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana4", clicks=0, owner_id=regular_user.id)
        data = client.get("/analytics/ana4", headers=auth(user_token)).json()
        assert data["total_clicks"] == 0


# Device breakdown 

class TestAnalyticsDeviceBreakdown:

    def test_device_breakdown_counts_correctly(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana5", owner_id=regular_user.id)
        _seed_clicks(session, "ana5", [
            {"device_type": "mobile"},
            {"device_type": "mobile"},
            {"device_type": "desktop"},
            {"device_type": "bot"},
        ])
        data = client.get("/analytics/ana5", headers=auth(user_token)).json()
        breakdown = data["device_breakdown"]
        assert breakdown.get("mobile") == 2
        assert breakdown.get("desktop") == 1
        assert breakdown.get("bot") == 1

    def test_device_breakdown_empty_when_no_clicks(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana6", owner_id=regular_user.id)
        data = client.get("/analytics/ana6", headers=auth(user_token)).json()
        assert data["device_breakdown"] == {}


# Referrer tracking

class TestAnalyticsReferrers:

    def test_top_referrers_sorted_by_count(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana7", owner_id=regular_user.id)
        _seed_clicks(session, "ana7", [
            {"referrer": "https://google.com"},
            {"referrer": "https://google.com"},
            {"referrer": "https://twitter.com"},
        ])
        data = client.get("/analytics/ana7", headers=auth(user_token)).json()
        referrers = data["top_referrers"]
        assert len(referrers) >= 1
        # google should be first (most clicks)
        assert referrers[0]["referrer"] == "https://google.com"
        assert referrers[0]["count"] == 2

    def test_null_referrers_excluded_or_labelled(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana8", owner_id=regular_user.id)
        _seed_clicks(session, "ana8", [
            {"referrer": None},
            {"referrer": None},
        ])
        data = client.get("/analytics/ana8", headers=auth(user_token)).json()
        # Should not crash; direct traffic may appear as "Direct" or be omitted
        assert isinstance(data["top_referrers"], list)


#  Recent clicks 

class TestAnalyticsRecentClicks:

    def test_recent_clicks_is_list(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana9", owner_id=regular_user.id)
        data = client.get("/analytics/ana9", headers=auth(user_token)).json()
        assert isinstance(data["recent_clicks"], list)

    def test_recent_clicks_contain_expected_fields(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana10", owner_id=regular_user.id)
        _seed_clicks(session, "ana10", [{"device_type": "mobile", "referrer": "https://t.co"}])
        data = client.get("/analytics/ana10", headers=auth(user_token)).json()
        click = data["recent_clicks"][0]
        assert "clicked_at" in click
        assert "device_type" in click
        assert "referrer" in click

    def test_recent_clicks_limited_to_50(
        self, client: TestClient, session: Session, user_token: str, regular_user
    ):
        _seed_url(session, "ana11", owner_id=regular_user.id)
        _seed_clicks(session, "ana11", [{"device_type": "desktop"}] * 60)
        data = client.get("/analytics/ana11", headers=auth(user_token)).json()
        assert len(data["recent_clicks"]) <= 50


# Edge cases 

class TestAnalyticsEdgeCases:

    def test_nonexistent_code_returns_404(
        self, client: TestClient, user_token: str
    ):
        resp = client.get("/analytics/nope999", headers=auth(user_token))
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client: TestClient, session: Session):
        _seed_url(session, "ana12")
        resp = client.get("/analytics/ana12")
        assert resp.status_code == 401

    def test_other_users_url_returns_403(
        self,
        client: TestClient,
        session: Session,
        user_token: str,
        admin_user,
    ):
        """A regular user should not be able to view another user's analytics."""
        # URL owned by admin (id != regular user id)
        _seed_url(session, "ana13", owner_id=admin_user.id)
        resp = client.get("/analytics/ana13", headers=auth(user_token))
        # Depending on implementation: 403 or 404 are both acceptable
        assert resp.status_code in (403, 404)

    def test_admin_can_view_any_url_analytics(
        self,
        client: TestClient,
        session: Session,
        admin_token: str,
        regular_user,
    ):
        _seed_url(session, "ana14", owner_id=regular_user.id)
        resp = client.get("/analytics/ana14", headers=auth(admin_token))
        assert resp.status_code == 200
