"""Thread-safe quota registry returning immutable local snapshots."""

from __future__ import annotations

from threading import RLock

from .errors import QuotaNotFoundError, RateLimitError
from .models import RateLimitSnapshot


class QuotaRegistry:
    """Store exactly one immutable quota snapshot per provider and scope."""

    def __init__(self) -> None:
        self._snapshots: dict[tuple[str, str], RateLimitSnapshot] = {}
        self._lock = RLock()

    def register(self, snapshot: RateLimitSnapshot) -> None:
        """Register a quota snapshot and reject duplicate provider/scope pairs."""
        key = (snapshot.provider, snapshot.scope)
        with self._lock:
            if key in self._snapshots:
                raise RateLimitError(
                    f"Quota '{snapshot.provider}/{snapshot.scope}' exists"
                )
            self._snapshots[key] = snapshot

    def get(self, provider: str, scope: str = "provider") -> RateLimitSnapshot:
        """Return a quota snapshot or raise a typed missing-quota error."""
        key = (provider, scope)
        with self._lock:
            try:
                return self._snapshots[key]
            except KeyError as error:
                raise QuotaNotFoundError(
                    f"Quota '{provider}/{scope}' is not registered"
                ) from error

    def list(self) -> list[RateLimitSnapshot]:
        """Return snapshots in stable provider then scope order."""
        with self._lock:
            return [self._snapshots[key] for key in sorted(self._snapshots)]

    def update(self, snapshot: RateLimitSnapshot) -> None:
        """Replace a registered snapshot; missing quotas are explicit errors."""
        key = (snapshot.provider, snapshot.scope)
        with self._lock:
            if key not in self._snapshots:
                raise QuotaNotFoundError(
                    f"Quota '{snapshot.provider}/{snapshot.scope}' is not registered"
                )
            self._snapshots[key] = snapshot

    def reset(self, provider: str, scope: str = "provider") -> RateLimitSnapshot:
        """Reset observed usage while preserving registered quota limits."""
        snapshot = self.get(provider, scope)
        reset = RateLimitSnapshot(
            provider=snapshot.provider,
            scope=snapshot.scope,
            requests_per_second=snapshot.requests_per_second,
            requests_per_minute=snapshot.requests_per_minute,
            tokens_per_minute=snapshot.tokens_per_minute,
            remaining_requests=snapshot.requests_per_minute,
            remaining_tokens=snapshot.tokens_per_minute,
        )
        self.update(reset)
        return reset

    def clear(self) -> None:
        """Remove all local quota snapshots."""
        with self._lock:
            self._snapshots.clear()
