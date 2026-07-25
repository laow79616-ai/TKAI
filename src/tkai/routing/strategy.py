"""Pluggable provider selection strategies for immutable routing candidates."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from tkai.circuit_breaker import CircuitState
from tkai.health import HealthStatus

from .models import ProviderMetadata, RoutingCandidate, RoutingDecision
from .policies import RoutingPolicy


class RoutingStrategy(ABC):
    """Select a provider from already-enriched candidates without side effects."""

    @abstractmethod
    def select_provider(
        self,
        candidates: Sequence[RoutingCandidate],
        *,
        required_capabilities: frozenset[str] = frozenset(),
    ) -> RoutingDecision:
        """Return one explicit selection or an explainable no-match decision."""

    @abstractmethod
    def score_provider(self, candidate: RoutingCandidate) -> tuple[float, ...]:
        """Return a deterministic sort key for an eligible candidate."""

    @abstractmethod
    def supports(
        self, metadata: ProviderMetadata, required_capabilities: frozenset[str]
    ) -> bool:
        """Return whether metadata declares every requested capability."""


class CostAwareStrategy(RoutingStrategy):
    """Select healthy, capable providers by cost, priority, and stable weight."""

    def __init__(self, policy: RoutingPolicy | None = None) -> None:
        self.policy = policy or RoutingPolicy()

    def supports(
        self, metadata: ProviderMetadata, required_capabilities: frozenset[str]
    ) -> bool:
        """Require every requested capability to be declared by the provider."""
        return required_capabilities.issubset(metadata.capabilities)

    def score_provider(self, candidate: RoutingCandidate) -> tuple[float, ...]:
        """Score by cost, then HALF_OPEN penalty, priority, weight, and name."""
        return (
            candidate.metadata.cost_per_1k,
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
        """Apply passive filters and return an explainable cost-aware choice."""
        eligible = [
            item
            for item in candidates
            if item.breaker_state is not CircuitState.OPEN
            and (
                self.policy.allow_half_open
                or item.breaker_state is not CircuitState.HALF_OPEN
            )
            and (
                not self.policy.require_healthy
                or item.health_status is HealthStatus.HEALTHY
            )
            and self.supports(item.metadata, required_capabilities)
        ]
        names = tuple(item.metadata.provider for item in candidates)
        if not eligible:
            return RoutingDecision(
                None,
                names,
                "No candidate satisfies breaker, health, and capability requirements",
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
        return RoutingDecision(
            metadata.provider,
            tuple(item.metadata.provider for item in eligible),
            "Selected lowest-cost eligible provider; ties use breaker state, "
            "priority, and weight",
            metadata.cost_per_1k,
            metadata.priority,
            metadata.weight,
            selected.health_status,
            selected.breaker_state,
        )
