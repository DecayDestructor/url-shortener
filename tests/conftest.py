"""
conftest.py — shared fixtures for the snip.ly test suite.
All external dependencies (Redis, PostgreSQL) are fully mocked.
No real network connections are made during tests.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from datetime import datetime, timezone

from app.main import app
from app.db.database import get_session
from app.db.models import URL, User, ClickEvent
from app.core.auth import create_access_token, hash_password


# In-memory SQLite engine (replaces PostgreSQL) 

@pytest.fixture(name="engine")
def engine_fixture():
    """Fresh in-memory SQLite DB per test — no state leakage."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


# Mock Redis client

@pytest.fixture(name="mock_redis")
def mock_redis_fixture():
    """
    Returns a MagicMock that mimics the redis_client interface used in url.py.
    Patched globally so every import of redis_client in the app uses this mock.
    """
    store = {}

    mock = MagicMock()

    # incr: increment and return new value
    def _incr(key):
        store[key] = store.get(key, 0) + 1
        return store[key]

    # get: return stored value or None
    def _get(key):
        return store.get(key)

    # set / setex: store value
    def _setex(key, ttl, value):
        store[key] = value

    def _set(key, value, ex=None):
        store[key] = value

    # delete
    def _delete(*keys):
        for k in keys:
            store.pop(k, None)

    # expire: no-op in mock
    def _expire(key, ttl):
        pass

    # zadd, zincrby, zrevrange, zrem
    trending = {}

    def _zincrby(name, amount, member):
        trending[member] = trending.get(member, 0) + amount
        return trending[member]

    def _zrevrange(name, start, end, withscores=False):
        sorted_items = sorted(trending.items(), key=lambda x: -x[1])
        sliced = sorted_items[start: end + 1 if end >= 0 else None]
        if withscores:
            return [(k, v) for k, v in sliced]
        return [k for k, _ in sliced]

    def _zrem(name, member):
        trending.pop(member, None)

    mock.incr.side_effect = _incr
    mock.get.side_effect = _get
    mock.setex.side_effect = _setex
    mock.set.side_effect = _set
    mock.delete.side_effect = _delete
    mock.expire.side_effect = _expire
    mock.zincrby.side_effect = _zincrby
    mock.zrevrange.side_effect = _zrevrange
    mock.zrem.side_effect = _zrem

    with patch("app.core.redis.redis_client", mock), \
         patch("app.routes.url.redis_client", mock), \
         patch("app.core.rate_limit.redis_client", mock), \
         patch("app.tasks.click_sync.redis_client", mock):
        yield mock, store


# Seeded user fixtures 

@pytest.fixture(name="regular_user")
def regular_user_fixture(session):
    user = User(
        email="user@test.com",
        username="testuser",
        hashed_password=hash_password("password123"),
        is_admin=False,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="admin_user")
def admin_user_fixture(session):
    user = User(
        email="admin@test.com",
        username="adminuser",
        hashed_password=hash_password("adminpass"),
        is_admin=True,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# JWT token helpers 

@pytest.fixture(name="user_token")
def user_token_fixture(regular_user):
    return create_access_token({"sub": str(regular_user.id), "is_admin": False})


@pytest.fixture(name="admin_token")
def admin_token_fixture(admin_user):
    return create_access_token({"sub": str(admin_user.id), "is_admin": True})


# TestClient with overridden DB 

@pytest.fixture(name="client")
def client_fixture(session, mock_redis):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()
