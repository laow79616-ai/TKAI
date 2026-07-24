"""Thread-safe local Publisher registry for reference descriptors only."""

from __future__ import annotations

from threading import RLock

from .errors import PublisherConflictError, PublisherNotFoundError
from .models import Publisher, PublisherTier


class PublisherRegistry:
    """Store immutable Publisher declarations without persistence or global state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._publishers: dict[str, Publisher] = {}

    def register(self, publisher: Publisher) -> Publisher:
        """Register a publisher descriptor or raise for a duplicate explicit id."""
        with self._lock:
            if publisher.publisher_id in self._publishers:
                raise PublisherConflictError(publisher.publisher_id)
            self._publishers[publisher.publisher_id] = publisher
            return publisher

    def unregister(self, publisher_id: str) -> Publisher:
        """Remove one publisher declaration without deleting external resources."""
        with self._lock:
            try:
                return self._publishers.pop(publisher_id)
            except KeyError as exc:
                raise PublisherNotFoundError(publisher_id) from exc

    def get(self, publisher_id: str) -> Publisher:
        """Return one immutable local publisher descriptor."""
        with self._lock:
            try:
                return self._publishers[publisher_id]
            except KeyError as exc:
                raise PublisherNotFoundError(publisher_id) from exc

    def list(self, tier: PublisherTier | None = None) -> tuple[Publisher, ...]:
        """Return local descriptors in stable publisher-id order."""
        with self._lock:
            return tuple(
                publisher
                for _, publisher in sorted(self._publishers.items())
                if tier is None or publisher.tier is tier
            )

    def snapshot(self) -> tuple[Publisher, ...]:
        """Return a stable read-only local publisher snapshot."""
        return self.list()

    def clear(self) -> None:
        """Idempotently clear reference-only in-memory publisher declarations."""
        with self._lock:
            self._publishers.clear()
