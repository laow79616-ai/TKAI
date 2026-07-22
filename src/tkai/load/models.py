"""Immutable, JSON-ready provider load snapshots."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from math import isfinite


class LoadStatus(str, Enum):
    """Coarse, local process load classification."""

    UNKNOWN = "unknown"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    SATURATED = "saturated"


@dataclass(frozen=True, slots=True)
class ProviderLoadSnapshot:
    """Read-only local load state for one provider without global-server claims."""

    provider: str
    active_requests: int = 0
    pending_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float = 0.0
    utilization: float = 0.0
    status: LoadStatus = LoadStatus.UNKNOWN
    last_updated: datetime | None = None

    def __post_init__(self) -> None:
        """Validate numeric bounds and normalize supplied timestamps to UTC."""
        if not self.provider:
            raise ValueError("provider must not be empty")
        counts = (
            self.active_requests,
            self.pending_requests,
            self.completed_requests,
            self.failed_requests,
            self.timeout_requests,
        )
        if any(value < 0 for value in counts):
            raise ValueError("load counters must not be negative")
        floating = (
            self.average_latency_ms,
            self.p95_latency_ms,
            self.p99_latency_ms,
            self.error_rate,
            self.utilization,
        )
        if not all(isfinite(value) for value in floating):
            raise ValueError("load metrics must be finite")
        if min(self.average_latency_ms, self.p95_latency_ms, self.p99_latency_ms) < 0:
            raise ValueError("latency metrics must not be negative")
        if not 0.0 <= self.error_rate <= 1.0:
            raise ValueError("error_rate must be between zero and one")
        if not 0.0 <= self.utilization <= 1.0:
            raise ValueError("utilization must be between zero and one")
        if self.last_updated is not None:
            if self.last_updated.tzinfo is None:
                raise ValueError("last_updated must be timezone-aware")
            object.__setattr__(
                self, "last_updated", self.last_updated.astimezone(timezone.utc)
            )

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-ready snapshot with ISO-8601 UTC timestamps."""
        data = asdict(self)
        data["status"] = self.status.value
        data["last_updated"] = (
            self.last_updated.isoformat() if self.last_updated is not None else None
        )
        return data
