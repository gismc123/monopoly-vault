"""A small in-memory limiter for sign-in and sign-up attempts.

The API runs as a single process, so counting in memory is enough. Counts reset
when the API restarts, which is fine for slowing down password guessing.
"""
import math
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self):
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, window: float, now: float) -> deque[float]:
        hits = self._hits[key]
        while hits and hits[0] <= now - window:
            hits.popleft()
        return hits

    def check(self, key: str, limit: int, window_seconds: float) -> None:
        """Raise 429 if `key` already has `limit` hits inside the window."""
        now = time.monotonic()
        with self._lock:
            hits = self._prune(key, window_seconds, now)
            if len(hits) >= limit:
                retry_after = math.ceil(hits[0] + window_seconds - now)
                minutes = max(1, math.ceil(retry_after / 60))
                raise HTTPException(
                    429,
                    f"Too many attempts. Try again in {minutes} minute{'s' if minutes != 1 else ''}.",
                    headers={"Retry-After": str(retry_after)},
                )

    def hit(self, key: str) -> None:
        with self._lock:
            self._hits[key].append(time.monotonic())

    def clear(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    # nginx passes the real client address (see web/nginx.conf); uvicorn applies it.
    return request.client.host if request.client else "unknown"
