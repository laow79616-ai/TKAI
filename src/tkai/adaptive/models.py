"""Immutable, JSON-ready data for process-local adaptive routing."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from types import MappingProxyType


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _number(value: float, name: str, *, minimum: float = 0.0) -> None:
    if not isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and at least {minimum}")


@dataclass(frozen=True, slots=True)
class ProviderSignal:
    """One safe, request-body-free result from an actual provider attempt."""

    provider: str
    timestamp: datetime
    latency_ms: float = 0.0
    success: bool = True
    error_type: str | None = None
    cost: float = 0.0
    load: float = 0.0
    available: bool = True
    breaker_open: bool = False
    rate_limited: bool = False
    retry_count: int = 0
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.provider:
            raise ValueError("provider must not be empty")
        _number(self.latency_ms, "latency_ms")
        _number(self.cost, "cost")
        _number(self.load, "load")
        if self.load > 1.0:
            raise ValueError("load must not exceed one")
        if self.retry_count < 0:
            raise ValueError("retry_count must not be negative")
        object.__setattr__(self, "timestamp", _utc(self.timestamp))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error_type": self.error_type,
            "cost": self.cost,
            "load": self.load,
            "available": self.available,
            "breaker_open": self.breaker_open,
            "rate_limited": self.rate_limited,
            "retry_count": self.retry_count,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProviderStatistics:
    """Bounded-history aggregate with deterministic latency statistics."""

    provider: str
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    error_rate: float = 0.0
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    average_cost: float = 0.0
    current_load: float = 0.0
    last_updated: datetime | None = None
    sample_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "average_latency_ms": self.average_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "average_cost": self.average_cost,
            "current_load": self.current_load,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated is not None else None
            ),
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True, slots=True)
class ProviderScore:
    """Explainable normalized score for exactly one candidate provider."""

    provider: str
    total_score: float
    latency_score: float
    reliability_score: float
    cost_score: float
    load_score: float
    health_score: float
    confidence: float
    eligible: bool
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "total_score": self.total_score,
            "latency_score": self.latency_score,
            "reliability_score": self.reliability_score,
            "cost_score": self.cost_score,
            "load_score": self.load_score,
            "health_score": self.health_score,
            "confidence": self.confidence,
            "eligible": self.eligible,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """Stable adaptive ranking result independent of legacy routing decisions."""

    selected_provider: str | None
    candidates: tuple[str, ...]
    scores: tuple[ProviderScore, ...]
    reason: str
    strategy: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fallback_used: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_provider": self.selected_provider,
            "candidates": list(self.candidates),
            "scores": [score.to_dict() for score in self.scores],
            "reason": self.reason,
            "strategy": self.strategy,
            "timestamp": _utc(self.timestamp).isoformat(),
            "fallback_used": self.fallback_used,
        }
