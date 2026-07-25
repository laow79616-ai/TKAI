"""Replaceable deterministic classification of local provider load."""

from __future__ import annotations

from dataclasses import dataclass

from .models import LoadStatus, ProviderLoadSnapshot


@dataclass(frozen=True, slots=True)
class LoadThresholds:
    """Configurable local process thresholds for the default evaluator."""

    low_utilization: float = 0.30
    normal_utilization: float = 0.70
    high_utilization: float = 0.90
    high_pending_requests: int = 10
    high_latency_ms: float = 1000.0
    high_error_rate: float = 0.20

    def __post_init__(self) -> None:
        """Ensure ordered finite utilization boundaries and non-negative signals."""
        if not (
            0
            <= self.low_utilization
            <= self.normal_utilization
            <= self.high_utilization
            <= 1
        ):
            raise ValueError(
                "utilization thresholds must be ordered between zero and one"
            )
        if self.high_pending_requests < 0 or self.high_latency_ms < 0:
            raise ValueError("load thresholds must not be negative")
        if not 0 <= self.high_error_rate <= 1:
            raise ValueError("high_error_rate must be between zero and one")


class LoadEvaluator:
    """Classify snapshots using local counters, latency, error rate, and utilization."""

    def __init__(self, thresholds: LoadThresholds | None = None) -> None:
        self.thresholds = thresholds or LoadThresholds()

    def evaluate(self, snapshot: ProviderLoadSnapshot) -> LoadStatus:
        """Return one stable status without changing the supplied snapshot."""
        if snapshot.last_updated is None:
            return LoadStatus.UNKNOWN
        thresholds = self.thresholds
        if snapshot.utilization >= thresholds.high_utilization:
            return LoadStatus.SATURATED
        if (
            snapshot.utilization >= thresholds.normal_utilization
            or snapshot.pending_requests >= thresholds.high_pending_requests
            or snapshot.average_latency_ms >= thresholds.high_latency_ms
            or snapshot.error_rate >= thresholds.high_error_rate
        ):
            return LoadStatus.HIGH
        if snapshot.utilization < thresholds.low_utilization:
            return LoadStatus.LOW
        return LoadStatus.NORMAL
