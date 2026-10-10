"""Sign-in and sign-up rate limiting."""
import pytest
from fastapi import HTTPException

from app.config import get_settings


def login(client, username, password):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_too_many_wrong_passwords_pauses_sign_in(ivan):
    client = ivan.client
    for _ in range(10):
        assert login(client, "ivan", "wrong-password").status_code == 401

    blocked = login(client, "ivan", "password123")  # even the right password waits
    assert blocked.status_code == 429
    assert "Too many attempts" in blocked.json()["detail"]
    assert int(blocked.headers["Retry-After"]) > 0


def test_a_successful_sign_in_resets_the_count(ivan):
    client = ivan.client
    for _ in range(9):
        login(client, "ivan", "wrong-password")
    assert login(client, "ivan", "password123").status_code == 200
    for _ in range(9):
        assert login(client, "ivan", "wrong-password").status_code == 401


def test_one_users_lockout_does_not_block_another(ivan, ebony):
    for _ in range(10):
        login(ivan.client, "ivan", "wrong-password")
    assert login(ivan.client, "ivan", "password123").status_code == 429
    assert login(ebony.client, "ebony", "password123").status_code == 200


def test_guessing_many_usernames_from_one_ip_is_limited(client):
    for i in range(30):
        assert login(client, f"nobody{i}", "guess").status_code == 401
    assert login(client, "someone-else", "guess").status_code == 429


def test_sign_ups_per_ip_are_limited(client, monkeypatch):
    monkeypatch.setenv("SIGNUPS_PER_IP_PER_HOUR", "2")
    get_settings.cache_clear()
    for i in range(2):
        r = client.post("/api/auth/register", json={"name": "A", "username": f"user{i}", "password": "password123"})
        assert r.status_code == 200
    r = client.post("/api/auth/register", json={"name": "A", "username": "user9", "password": "password123"})
    assert r.status_code == 429


def test_window_expiry(monkeypatch):
    """Hits older than the window no longer count."""
    from app import ratelimit

    now = [1000.0]
    monkeypatch.setattr(ratelimit.time, "monotonic", lambda: now[0])
    limiter = ratelimit.RateLimiter()
    for _ in range(3):
        limiter.hit("k")
    with pytest.raises(HTTPException):
        limiter.check("k", 3, 60)
    now[0] += 61
    limiter.check("k", 3, 60)  # no error
