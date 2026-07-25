"""Pluggable local rate-limit strategies and an opt-in routing composition."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import RLock

from tkai.routing import (
    ProviderMetadata,
    RoutingCandidate,
    RoutingDecision,
    RoutingStrategy,
)

from .errors import QuotaNotFoundError
from .models import RateLimitSnapshot
from .registry import QuotaRegistry

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    """Return the default timezone-aware strategy clock."""
    return datetime.now(timezone.utc)


class RateLimitStrategy(ABC):
    """Manage quota consumption without owning registry or event publication."""

    @abstractmethod
    def allow(
        self,
        snapshot: RateLimitSnapshot,
        *,
        tokens: int = 0,
        now: datetime | None = None,
    ) -> bool:
        """Return whether a request can be consumed within local quota limits."""

    @abstractmethod
    def consume(
        self,
        snapshot: RateLimitSnapshot,
        *,
        tokens: int = 0,
        now: datetime | None = None,
    ) -> RateLimitSnapshot:
        """Record one permitted request and return a replacement immutable snapshot."""

    @abstractmethod
    def reset(
        self, snapshot: RateLimitSnapshot, *, now: datetime | None = None
    ) -> RateLimitSnapshot:
        """Reset strategy-owned local windows and return a fresh snapshot."""


class TokenBucketStrategy(RateLimitStrategy, ABC):
    """Reserved interface for future token-bucket algorithms; no algorithm yet."""


class SlidingWindowStrategy(RateLimitStrategy):
    """Use bounded timestamp deques for deterministic rolling quota windows."""

    def __init__(self, clock: Clock = _utc_now) -> None:
        self._clock = clock
        self._requests: dict[tuple[str, str], deque[datetime]] = {}
        self._tokens: dict[tuple[str, str], deque[tuple[datetime, int]]] = {}
        self._lock = RLock()

    def allow(
        self,
        snapshot: RateLimitSnapshot,
        *,
        tokens: int = 0,
        now: datetime | None = None,
    ) -> bool:
        """Check one-second, one-minute, and token-minute rolling quota windows."""
        if tokens < 0:
            return False
        with self._lock:
            current = now or self._clock()
            requests, token_entries = self._prune(snapshot, current)
            second_count = sum(
                item > current - timedelta(seconds=1) for item in requests
            )
            if (
                snapshot.requests_per_second
                and second_count >= snapshot.requests_per_second
            ):
                return False
            if (
                snapshot.requests_per_minute
                and len(requests) >= snapshot.requests_per_minute
            ):
                return False
            token_count = sum(value for _, value in token_entries)
            return not (
                snapshot.tokens_per_minute
                and token_count + tokens > snapshot.tokens_per_minute
            )

    def consume(
        self,
        snapshot: RateLimitSnapshot,
        *,
        tokens: int = 0,
        now: datetime | None = None,
    ) -> RateLimitSnapshot:
        """Consume one request after checking quota and return updated capacity."""
        if not self.allow(snapshot, tokens=tokens, now=now):
            return self._refresh(snapshot, now or self._clock())
        with self._lock:
            current = now or self._clock()
            requests, token_entries = self._prune(snapshot, current)
            requests.append(current)
            token_entries.append((current, tokens))
            return self._refresh(snapshot, current)

    def reset(
        self, snapshot: RateLimitSnapshot, *, now: datetime | None = None
    ) -> RateLimitSnapshot:
        """Forget rolling windows for one provider/scope quota."""
        with self._lock:
            key = self._key(snapshot)
            self._requests.pop(key, None)
            self._tokens.pop(key, None)
            return self._refresh(snapshot, now or self._clock())

    def _refresh(self, snapshot: RateLimitSnapshot, now: datetime) -> RateLimitSnapshot:
        requests, token_entries = self._prune(snapshot, now)
        current_requests = len(requests)
        current_tokens = sum(value for _, value in token_entries)
        request_remaining = (
            max(0, snapshot.requests_per_minute - current_requests)
            if snapshot.requests_per_minute
            else 0
        )
        token_remaining = (
            max(0, snapshot.tokens_per_minute - current_tokens)
            if snapshot.tokens_per_minute
            else 0
        )
        reset_at = min((item + timedelta(minutes=1) for item in requests), default=None)
        return replace(
            snapshot,
            current_requests=current_requests,
            current_tokens=current_tokens,
            remaining_requests=request_remaining,
            remaining_tokens=token_remaining,
            reset_at=reset_at,
            last_updated=now,
        )

    def _prune(
        self, snapshot: RateLimitSnapshot, now: datetime
    ) -> tuple[deque[datetime], deque[tuple[datetime, int]]]:
        key = self._key(snapshot)
        requests = self._requests.setdefault(key, deque())
        token_entries = self._tokens.setdefault(key, deque())
        oldest = now - timedelta(minutes=1)
        while requests and requests[0] <= oldest:
            requests.popleft()
        while token_entries and token_entries[0][0] <= oldest:
            token_entries.popleft()
        return requests, token_entries

    @staticmethod
    def _key(snapshot: RateLimitSnapshot) -> tuple[str, str]:
        return (snapshot.provider, snapshot.scope)


class FixedWindowStrategy(RateLimitStrategy):
    """Use deterministic wall-clock one-minute quota windows per provider scope."""

    def __init__(self, clock: Clock = _utc_now) -> None:
        self._clock = clock
        self._windows: dict[tuple[str, str], tuple[datetime, int, int]] = {}
        self._second_windows: dict[tuple[str, str], tuple[datetime, int]] = {}
        self._lock = RLock()

    def allow(
        self,
        snapshot: RateLimitSnapshot,
        *,
        tokens: int = 0,
        now: datetime | None = None,
    ) -> bool:
        """Check the current fixed one-minute request and token quota window."""
        if tokens < 0:
            return False
        with self._lock:
            current = now or self._clock()
            _, requests, token_count = self._window(snapshot, current)
            _, second_requests = self._second_window(snapshot, current)
            return not (
                (
                    snapshot.requests_per_second
                    and second_requests >= snapshot.requests_per_second
                )
                or (
                    snapshot.requests_per_minute
                    and requests >= snapshot.requests_per_minute
                )
                or (
                    snapshot.tokens_per_minute
                    and token_count + tokens > snapshot.tokens_per_minute
                )
            )

    def consume(
        self,
        snapshot: RateLimitSnapshot,
        *,
        tokens: int = 0,
        now: datetime | None = None,
    ) -> RateLimitSnapshot:
        """Consume one fixed-window request when capacity allows it."""
        current = now or self._clock()
        if not self.allow(snapshot, tokens=tokens, now=current):
            return self._refresh(snapshot, current)
        with self._lock:
            start, requests, token_count = self._window(snapshot, current)
            self._windows[self._key(snapshot)] = (
                start,
                requests + 1,
                token_count + tokens,
            )
            second_start, second_requests = self._second_window(snapshot, current)
            self._second_windows[self._key(snapshot)] = (
                second_start,
                second_requests + 1,
            )
            return self._refresh(snapshot, current)

    def reset(
        self, snapshot: RateLimitSnapshot, *, now: datetime | None = None
    ) -> RateLimitSnapshot:
        """Clear one fixed window and return a replacement local snapshot."""
        with self._lock:
            self._windows.pop(self._key(snapshot), None)
            self._second_windows.pop(self._key(snapshot), None)
            return self._refresh(snapshot, now or self._clock())

    def _refresh(self, snapshot: RateLimitSnapshot, now: datetime) -> RateLimitSnapshot:
        start, requests, token_count = self._window(snapshot, now)
        return replace(
            snapshot,
            current_requests=requests,
            current_tokens=token_count,
            remaining_requests=(
                max(0, snapshot.requests_per_minute - requests)
                if snapshot.requests_per_minute
                else 0
            ),
            remaining_tokens=(
                max(0, snapshot.tokens_per_minute - token_count)
                if snapshot.tokens_per_minute
                else 0
            ),
            reset_at=start + timedelta(minutes=1),
            last_updated=now,
        )

    def _window(
        self, snapshot: RateLimitSnapshot, now: datetime
    ) -> tuple[datetime, int, int]:
        key = self._key(snapshot)
        start = now.replace(second=0, microsecond=0)
        current = self._windows.get(key)
        if current is None or current[0] != start:
            current = (start, 0, 0)
            self._windows[key] = current
        return current

    def _second_window(
        self, snapshot: RateLimitSnapshot, now: datetime
    ) -> tuple[datetime, int]:
        key = self._key(snapshot)
        start = now.replace(microsecond=0)
        current = self._second_windows.get(key)
        if current is None or current[0] != start:
            current = (start, 0)
            self._second_windows[key] = current
        return current

    @staticmethod
    def _key(snapshot: RateLimitSnapshot) -> tuple[str, str]:
        return (snapshot.provider, snapshot.scope)


class RateLimitAwareStrategy(RoutingStrategy):
    """Compose any existing routing strategy with non-consuming quota filtering."""

    def __init__(
        self,
        registry: QuotaRegistry,
        base_strategy: RoutingStrategy,
        quota_strategy: RateLimitStrategy,
    ) -> None:
        self.registry = registry
        self.base_strategy = base_strategy
        self.quota_strategy = quota_strategy

    def supports(
        self, metadata: ProviderMetadata, required_capabilities: frozenset[str]
    ) -> bool:
        """Delegate capability checks to the wrapped unchanged routing strategy."""
        return self.base_strategy.supports(metadata, required_capabilities)

    def score_provider(self, candidate: RoutingCandidate) -> tuple[float, ...]:
        """Delegate stable score computation to the wrapped routing strategy."""
        return self.base_strategy.score_provider(candidate)

    def select_provider(
        self,
        candidates: Sequence[RoutingCandidate],
        *,
        required_capabilities: frozenset[str] = frozenset(),
    ) -> RoutingDecision:
        """Exclude only registered quotas that currently reject another request."""
        eligible = [item for item in candidates if self._allows(item.metadata.provider)]
        return self.base_strategy.select_provider(
            eligible, required_capabilities=required_capabilities
        )

    def _allows(self, provider: str) -> bool:
        try:
            snapshot = self.registry.get(provider)
        except QuotaNotFoundError:
            return True
        return self.quota_strategy.allow(snapshot)
