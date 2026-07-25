"""Replaceable, deterministic single-process request limiting."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """Immutable result of one caller-provided rate-limit key check."""

    allowed: bool
    remaining: int


class RateLimiter(Protocol):
    """Boundary for local or future distributed rate limiting implementations."""

    def allow(self, key: str) -> RateLimitDecision: ...


class InMemoryRateLimiter:
    """Thread-safe fixed-window limiter; it holds no background worker."""

    def __init__(self, requests: int, window_seconds: float) -> None:
        self._requests = requests
        self._window_seconds = window_seconds
        self._lock = RLock()
        self._buckets: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> RateLimitDecision:
        """Allow a request if its explicit key has remaining capacity."""
        now = monotonic()
        with self._lock:
            started, count = self._buckets.get(key, (now, 0))
            if now - started >= self._window_seconds:
                started, count = now, 0
            if count >= self._requests:
                return RateLimitDecision(False, 0)
            count += 1
            self._buckets[key] = (started, count)
            return RateLimitDecision(True, self._requests - count)
