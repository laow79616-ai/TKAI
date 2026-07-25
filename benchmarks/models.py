"""Immutable, serialization-safe benchmark result models."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Stable aggregate timing result suitable for release-to-release comparison."""

    operations: int = 0
    elapsed_seconds: float = 0.0
    ops_per_second: float = 0.0
    mean_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if self.operations < 0:
            raise ValueError("operations must not be negative")
        values = tuple(asdict(self).values())[1:]
        if not all(isfinite(value) and value >= 0.0 for value in values):
            raise ValueError("benchmark timing values must be finite and non-negative")

    def to_dict(self) -> dict[str, int | float]:
        """Return stable primitive values with no internal timer state."""
        return dict(asdict(self))

    def to_json(self) -> str:
        """Return deterministic JSON for storing or comparing offline runs."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
