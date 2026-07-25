"""Validated score weights for adaptive routing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class AdaptiveWeights:
    """Component weights; defaults are kept in this single public model."""

    reliability: float = 0.35
    latency: float = 0.25
    health: float = 0.20
    cost: float = 0.10
    load: float = 0.10

    def validate(self) -> None:
        values = tuple(asdict(self).values())
        if not all(isfinite(value) and value >= 0.0 for value in values):
            raise ValueError("adaptive weights must be finite and non-negative")
        if sum(values) <= 0.0:
            raise ValueError("at least one adaptive weight must be positive")

    def normalized(self) -> AdaptiveWeights:
        self.validate()
        total = sum(asdict(self).values())
        return AdaptiveWeights(
            **{name: value / total for name, value in asdict(self).items()}
        )

    def snapshot(self) -> dict[str, float]:
        return dict(asdict(self.normalized()))
