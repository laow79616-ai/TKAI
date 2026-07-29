"""Bounded read-only adapters for decision-evolution source systems."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .models import DecisionEvolutionContext

DECISION_SOURCES = (
    "decision_center",
    "strategy_center",
    "operations_planner",
    "autonomous_operation",
    "mission_engine",
    "governance_center",
    "knowledge_evolution",
    "learning_center",
    "intelligence_center",
    "optimization_center",
    "recovery_center",
    "risk_control",
    "business_intelligence_center",
    "performance_insights",
    "analytics_center",
)


class ReadOnlyDecisionSource(Protocol):
    def read_decisions(
        self,
        start: datetime,
        end: datetime,
        context: DecisionEvolutionContext,
        *,
        limit: int,
    ) -> tuple[dict[str, object], ...]: ...


class ReferenceOnlyDecisionSource:
    """Provides bounded references and deliberately exposes no mutation operation."""

    def __init__(self, source: str, service: object | None = None) -> None:
        if source not in DECISION_SOURCES:
            raise ValueError(f"Unsupported decision source: {source}")
        self.source = source
        self.service = service

    def read_decisions(
        self,
        start: datetime,
        end: datetime,
        context: DecisionEvolutionContext,
        *,
        limit: int,
    ) -> tuple[dict[str, object], ...]:
        if start >= end:
            raise ValueError("A valid bounded time range is required.")
        if not 1 <= limit <= 1_000:
            raise ValueError("Result limit must be within [1, 1000].")
        return (
            {
                "source": self.source,
                "tenant": context.tenant,
                "workspace": context.workspace,
                "reference": f"{self.source}://decision/{start.date().isoformat()}",
                "evidence_reference": (
                    f"integrity://{self.source}/{start.date().isoformat()}"
                ),
                "read_only": True,
                "reference_only": True,
                "execution": False,
                "publishing": False,
                "configuration_change": False,
                "restriction_bypass": False,
            },
        )


class ReferenceOnlyHandoff:
    """Produces an advisory URI; it cannot invoke the destination."""

    DESTINATIONS = frozenset(
        {"knowledge_evolution", "learning_center", "governance_center"}
    )

    @classmethod
    def create(cls, destination: str, recommendation_id: str) -> str:
        if destination not in cls.DESTINATIONS:
            raise ValueError("Unsupported advisory handoff destination.")
        if not recommendation_id:
            raise ValueError("Recommendation ID is required.")
        return f"advisory+reference://{destination}/{recommendation_id}"
