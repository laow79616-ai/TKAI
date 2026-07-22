"""Immutable, JSON-ready circuit breaker state models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum


class CircuitState(str, Enum):
    """The only states supported by the circuit breaker state machine."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True, slots=True)
class CircuitBreakerSnapshot:
    """Immutable provider breaker state suitable for diagnostics and JSON output."""

    provider: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    consecutive_failures: int = 0
    half_open_success_count: int = 0
    last_failure: datetime | None = None
    last_success: datetime | None = None
    opened_at: datetime | None = None
    half_open_since: datetime | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready snapshot without exposing implementation objects."""
        data = asdict(self)
        data["state"] = self.state.value
        for name in ("last_failure", "last_success", "opened_at", "half_open_since"):
            value = getattr(self, name)
            data[name] = value.isoformat() if value is not None else None
        return data
