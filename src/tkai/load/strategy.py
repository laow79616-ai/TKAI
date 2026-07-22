"""Optional load-aware strategy that preserves CostAwareStrategy behavior."""

from __future__ import annotations

from collections.abc import Sequence

from tkai.circuit_breaker import CircuitState
from tkai.health import HealthStatus
from tkai.routing import (
    CostAwareStrategy,
    ProviderMetadata,
    RoutingCandidate,
    RoutingDecision,
    RoutingStrategy,
)

from .errors import ProviderLoadNotFoundError
from .models import LoadStatus, ProviderLoadSnapshot
from .registry import LoadRegistry


class LoadAwareStrategy(RoutingStrategy):
    """Compose cost eligibility with deterministic process-local load scoring."""

    def __init__(
        self,
        load_registry: LoadRegistry,
        *,
        cost_strategy: CostAwareStrategy | None = None,
    ) -> None:
        self.load_registry = load_registry
        self.cost_strategy = cost_strategy or CostAwareStrategy()

    def supports(
        self, metadata: ProviderMetadata, required_capabilities: frozenset[str]
    ) -> bool:
        """Delegate capability declarations to the unchanged cost-aware strategy."""
        return self.cost_strategy.supports(metadata, required_capabilities)

    def score_provider(self, candidate: RoutingCandidate) -> tuple[float, ...]:
        """Return cost-first deterministic score enriched by process-local load."""
        snapshot = self._snapshot(candidate.metadata.provider)
        return (
            candidate.metadata.cost_per_1k,
            *self._load_score(snapshot),
            float(candidate.breaker_state is CircuitState.HALF_OPEN),
            float(-candidate.metadata.priority),
            float(-candidate.metadata.weight),
        )

    def select_provider(
        self,
        candidates: Sequence[RoutingCandidate],
        *,
        required_capabilities: frozenset[str] = frozenset(),
    ) -> RoutingDecision:
        """Filter passively then choose by cost, load, priority, weight, and name."""
        eligible = [
            item
            for item in candidates
            if item.breaker_state is not CircuitState.OPEN
            and (
                self.cost_strategy.policy.allow_half_open
                or item.breaker_state is not CircuitState.HALF_OPEN
            )
            and (
                not self.cost_strategy.policy.require_healthy
                or item.health_status is HealthStatus.HEALTHY
            )
            and self.supports(item.metadata, required_capabilities)
            and self._snapshot(item.metadata.provider).status
            is not LoadStatus.SATURATED
        ]
        known_low = any(
            self._snapshot(item.metadata.provider).status
            in {LoadStatus.LOW, LoadStatus.NORMAL}
            for item in eligible
        )
        if known_low:
            eligible = [
                item
                for item in eligible
                if self._snapshot(item.metadata.provider).status
                is not LoadStatus.UNKNOWN
            ]
        if not eligible:
            return RoutingDecision(
                None,
                tuple(item.metadata.provider for item in candidates),
                "No candidate satisfies breaker, health, capability, and load "
                "requirements",
                None,
                None,
                None,
                None,
                None,
            )
        selected = min(
            eligible,
            key=lambda item: (*self.score_provider(item), item.metadata.provider),
        )
        metadata = selected.metadata
        ordered = sorted(
            eligible,
            key=lambda item: (*self.score_provider(item), item.metadata.provider),
        )
        return RoutingDecision(
            metadata.provider,
            tuple(item.metadata.provider for item in ordered),
            "Selected by cost, local load, priority, weight, and stable name",
            metadata.cost_per_1k,
            metadata.priority,
            metadata.weight,
            selected.health_status,
            selected.breaker_state,
        )

    def _snapshot(self, provider: str) -> ProviderLoadSnapshot:
        """Treat unregistered local load as explicit UNKNOWN, never as low load."""
        try:
            return self.load_registry.get(provider)
        except ProviderLoadNotFoundError:
            return ProviderLoadSnapshot(provider)

    @staticmethod
    def _load_score(snapshot: ProviderLoadSnapshot) -> tuple[float, ...]:
        """Score lower active, pending, utilization, latency, and error values first."""
        status_penalty = {
            LoadStatus.LOW: 0.0,
            LoadStatus.NORMAL: 0.0,
            LoadStatus.HIGH: 1.0,
            LoadStatus.UNKNOWN: 2.0,
            LoadStatus.SATURATED: 3.0,
        }[snapshot.status]
        return (
            status_penalty,
            float(snapshot.active_requests),
            float(snapshot.pending_requests),
            snapshot.utilization,
            snapshot.average_latency_ms,
            snapshot.error_rate,
        )
