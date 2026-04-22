"""
test_rate_limit.py — Tests for Redis-backed rate limiting on POST /shorten.

Rate limit: 5 requests per 60-second window per IP.
Exceeding returns HTTP 429.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from redis.exceptions import RedisError


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


SHORTEN_PAYLOAD = {"original_url": "https://example.com"}


class TestRateLimiting:

    def test_first_request_succeeds(self, client: TestClient, user_token: str):
        resp = client.post("/shorten", json=SHORTEN_PAYLOAD, headers=auth(user_token))
        assert resp.status_code != 429

    def test_fifth_request_still_succeeds(self, client: TestClient, user_token: str):
        """
        Send exactly 5 requests — all should pass (limit is >5).
        We mock the rate limiter counter to return controlled values.
        """
        counter = {"val": 0}

        def fake_incr(key):
            counter["val"] += 1
            return counter["val"]

        with patch("app.core.rate_limit.redis_client") as mock_rl:
            mock_rl.incr.side_effect = fake_incr
            mock_rl.expire.return_value = True

            for i in range(5):
                resp = client.post(
                    "/shorten", json=SHORTEN_PAYLOAD, headers=auth(user_token)
                )
                assert resp.status_code != 429, f"Request {i+1} was rate-limited unexpectedly"

    def test_sixth_request_returns_429(self, client: TestClient, user_token: str):
        """
        Simulate a counter already at 6 (over the limit of 5).
        """
        with patch("app.core.rate_limit.redis_client") as mock_rl:
            mock_rl.incr.return_value = 6  # already over limit
            mock_rl.expire.return_value = True

            resp = client.post(
                "/shorten", json=SHORTEN_PAYLOAD, headers=auth(user_token)
            )
            assert resp.status_code == 429

    def test_429_response_has_detail(self, client: TestClient, user_token: str):
        with patch("app.core.rate_limit.redis_client") as mock_rl:
            mock_rl.incr.return_value = 10
            mock_rl.expire.return_value = True

            resp = client.post(
                "/shorten", json=SHORTEN_PAYLOAD, headers=auth(user_token)
            )
            assert resp.status_code == 429
            assert "detail" in resp.json()

    def test_redis_error_fails_open(self, client: TestClient, user_token: str):
        """
        If Redis is unreachable, rate limiting should fail open
        (i.e., NOT block the request — the route should still succeed).
        """
        with patch("app.core.rate_limit.redis_client") as mock_rl:
            mock_rl.incr.side_effect = RedisError("connection refused")

            resp = client.post(
                "/shorten", json=SHORTEN_PAYLOAD, headers=auth(user_token)
            )
            # Should NOT be 429 — fail open
            assert resp.status_code != 429

    def test_rate_limit_key_includes_client_ip(self, client: TestClient, user_token: str):
        """
        Verify that the rate limiter uses the client IP as the key.
        """
        captured_keys = []

        def capture_incr(key):
            captured_keys.append(key)
            return 1

        with patch("app.core.rate_limit.redis_client") as mock_rl:
            mock_rl.incr.side_effect = capture_incr
            mock_rl.expire.return_value = True

            client.post("/shorten", json=SHORTEN_PAYLOAD, headers=auth(user_token))

        assert any("rate_limit:" in k for k in captured_keys)
