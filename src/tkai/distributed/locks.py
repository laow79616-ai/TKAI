"""Thread-safe explicit local distributed-lock facade."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from tkai.observability import EventBus

from .backend import DistributedBackend
from .events import LockAcquired, LockReleased
from .models import LockSnapshot


class DistributedLock:
    """Lock contract used by local and future distributed backends."""

    def acquire(self) -> bool:
        raise NotImplementedError

    def release(self) -> bool:
        raise NotImplementedError

    def renew(self) -> bool:
        raise NotImplementedError


class LocalLock(DistributedLock):
    """Explicit named LocalBackend lock with optional local expiry metadata."""

    def __init__(
        self,
        backend: DistributedBackend,
        name: str,
        owner: str,
        *,
        ttl: timedelta | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.backend = backend
        self.name = name
        self.owner = owner
        self.ttl = ttl
        self.event_bus = event_bus
        self._expires_at: datetime | None = None
        self._acquired = False

    def acquire(self) -> bool:
        """Acquire once and emit a local event only after success."""
        self._acquired = self.backend.acquire_lock(self.name, self.owner)
        if self._acquired:
            self._renew_expiry()
            self._publish(LockAcquired(subject=self.name))
        return self._acquired

    def release(self) -> bool:
        """Release only the recorded owner lock and emit on success."""
        released = self.backend.release_lock(self.name, self.owner)
        if released:
            self._acquired = False
            self._expires_at = None
            self._publish(LockReleased(subject=self.name))
        return released

    def renew(self) -> bool:
        """Renew only an owned local lock; no remote lease protocol is implied."""
        if not self._acquired or not self.backend.acquire_lock(self.name, self.owner):
            return False
        self._renew_expiry()
        return True

    def snapshot(self) -> LockSnapshot:
        """Return immutable diagnostic lock state."""
        return LockSnapshot(
            self.name,
            self.owner if self._acquired else None,
            self._acquired,
            self._expires_at,
        )

    def _renew_expiry(self) -> None:
        if self.ttl is not None:
            self._expires_at = datetime.now(timezone.utc) + self.ttl

    def _publish(self, event: LockAcquired | LockReleased) -> None:
        if self.event_bus is not None:
            self.event_bus.publish(event)
