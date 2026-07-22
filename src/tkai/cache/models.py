"""Immutable cache entries and local backend statistics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class CacheEntry:
    """One immutable cached value with UTC expiry and access metadata."""

    key: str
    value: Any
    provider: str | None = None
    model: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    ttl: float | None = None
    hit_count: int = 0
    last_accessed: datetime | None = None

    def __post_init__(self) -> None:
        """Validate entry metadata and derive UTC timestamps from TTL safely."""
        if not self.key:
            raise ValueError("cache key must not be empty")
        if self.ttl is not None and self.ttl < 0:
            raise ValueError("ttl must not be negative")
        if self.hit_count < 0:
            raise ValueError("hit_count must not be negative")
        now = datetime.now(timezone.utc)
        created = self._utc(self.created_at) or now
        expires = self._utc(self.expires_at)
        if expires is None and self.ttl is not None:
            expires = created + timedelta(seconds=self.ttl)
        object.__setattr__(self, "created_at", created)
        object.__setattr__(self, "expires_at", expires)
        object.__setattr__(self, "last_accessed", self._utc(self.last_accessed))

    @staticmethod
    def _utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("cache timestamps must be timezone-aware")
        return value.astimezone(timezone.utc)

    def expired(self, now: datetime | None = None) -> bool:
        """Return whether the entry has reached its UTC expiry instant."""
        return (
            self.expires_at is not None
            and (now or datetime.now(timezone.utc)) >= self.expires_at
        )

    def accessed(self, now: datetime | None = None) -> CacheEntry:
        """Return a replacement entry with safe immutable hit metadata."""
        return CacheEntry(
            self.key,
            self.value,
            self.provider,
            self.model,
            self.created_at,
            self.expires_at,
            self.ttl,
            self.hit_count + 1,
            now or datetime.now(timezone.utc),
        )

    def to_dict(self) -> dict[str, object]:
        """Return JSON-ready metadata and value for compatible cached values."""
        data = asdict(self)
        for name in ("created_at", "expires_at", "last_accessed"):
            value = getattr(self, name)
            data[name] = value.isoformat() if value is not None else None
        return data


@dataclass(frozen=True, slots=True)
class CacheStatistics:
    """Stable backend observability counters maintained in local process memory."""

    hits: int = 0
    misses: int = 0
    expired: int = 0
    evicted: int = 0

    @property
    def hit_ratio(self) -> float:
        """Return zero for no reads and otherwise a deterministic hit ratio."""
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    @property
    def miss_ratio(self) -> float:
        """Return zero for no reads and otherwise a deterministic miss ratio."""
        total = self.hits + self.misses
        return self.misses / total if total else 0.0
