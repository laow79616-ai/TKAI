"""Immutable, JSON-ready local provider quota snapshots."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class RateLimitSnapshot:
    """One provider/scope quota and current local consumption observation."""

    provider: str
    scope: str = "provider"
    requests_per_second: int = 0
    requests_per_minute: int = 0
    tokens_per_minute: int = 0
    current_requests: int = 0
    current_tokens: int = 0
    remaining_requests: int = 0
    remaining_tokens: int = 0
    reset_at: datetime | None = None
    last_updated: datetime | None = None

    def __post_init__(self) -> None:
        """Validate non-negative local quota counters and normalize UTC times."""
        if not self.provider or not self.scope:
            raise ValueError("provider and scope must not be empty")
        values = (
            self.requests_per_second,
            self.requests_per_minute,
            self.tokens_per_minute,
            self.current_requests,
            self.current_tokens,
            self.remaining_requests,
            self.remaining_tokens,
        )
        if any(value < 0 for value in values):
            raise ValueError("quota values must not be negative")
        for name in ("reset_at", "last_updated"):
            value = getattr(self, name)
            if value is not None:
                if value.tzinfo is None:
                    raise ValueError(f"{name} must be timezone-aware")
                object.__setattr__(self, name, value.astimezone(timezone.utc))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-ready quota data with ISO-8601 UTC times."""
        data = asdict(self)
        for name in ("reset_at", "last_updated"):
            value = getattr(self, name)
            data[name] = value.isoformat() if value is not None else None
        return data
