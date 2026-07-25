"""Immutable routing metadata, candidates, and decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from math import isfinite

from tkai.circuit_breaker import CircuitState
from tkai.health import HealthStatus


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    """Static, provider-neutral data used by pluggable routing strategies."""

    provider: str
    priority: int = 0
    weight: int = 1
    prompt_cost_per_1k: float = 0.0
    completion_cost_per_1k: float = 0.0
    capabilities: frozenset[str] = frozenset()
    tags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Reject unusable identifiers, weights, and non-finite negative costs."""
        if not self.provider:
            raise ValueError("provider must not be empty")
        if self.weight < 1:
            raise ValueError("weight must be at least one")
        if (
            not isfinite(self.prompt_cost_per_1k)
            or not isfinite(self.completion_cost_per_1k)
            or self.prompt_cost_per_1k < 0
            or self.completion_cost_per_1k < 0
        ):
            raise ValueError("provider costs must be finite and non-negative")

    @property
    def cost_per_1k(self) -> float:
        """Return a stable total cost proxy when token mix is not specified."""
        return self.prompt_cost_per_1k + self.completion_cost_per_1k


@dataclass(frozen=True, slots=True)
class RoutingCandidate:
    """Metadata enriched with read-only Health and Breaker state snapshots."""

    metadata: ProviderMetadata
    health_status: HealthStatus
    breaker_state: CircuitState


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """Immutable, JSON-ready explanation of one routing selection attempt."""

    selected_provider: str | None
    candidate_providers: tuple[str, ...]
    reason: str
    cost: float | None
    priority: int | None
    weight: int | None
    health_status: HealthStatus | None
    breaker_state: CircuitState | None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-ready decision without registry internals."""
        data = asdict(self)
        data["health_status"] = (
            self.health_status.value if self.health_status is not None else None
        )
        data["breaker_state"] = (
            self.breaker_state.value if self.breaker_state is not None else None
        )
        data["timestamp"] = self.timestamp.isoformat()
        return data
