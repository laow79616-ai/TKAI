"""Immutable, JSON-safe local multi-region models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class Region:
    """Static local region metadata; endpoint is never contacted by this module."""

    region_id: str
    display_name: str = ""
    endpoint: str | None = None
    priority: int = 0
    enabled: bool = True
    healthy: bool = True
    latency_estimate_ms: float = 0.0
    capabilities: frozenset[str] = frozenset()
    tags: frozenset[str] = frozenset()
    metadata: Mapping[str, object] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.region_id:
            raise ValueError("region_id must not be empty")
        if not isfinite(self.latency_estimate_ms) or self.latency_estimate_ms < 0:
            raise ValueError("latency_estimate_ms must be finite and non-negative")
        if self.updated_at.tzinfo is None:
            raise ValueError("updated_at must be timezone-aware")
        object.__setattr__(self, "updated_at", self.updated_at.astimezone(timezone.utc))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, object]:
        return {
            "region_id": self.region_id,
            "display_name": self.display_name,
            "endpoint": self.endpoint,
            "priority": self.priority,
            "enabled": self.enabled,
            "healthy": self.healthy,
            "latency_estimate_ms": self.latency_estimate_ms,
            "capabilities": sorted(self.capabilities),
            "tags": sorted(self.tags),
            "metadata": dict(self.metadata),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class RegionDecision:
    """Stable, explainable result of an explicit region-routing call."""

    selected_region: str | None
    candidates: tuple[str, ...]
    reason: str
    fallback_used: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_region": self.selected_region,
            "candidates": list(self.candidates),
            "reason": self.reason,
            "fallback_used": self.fallback_used,
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
        }
