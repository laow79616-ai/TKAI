"""Bounded, read-only adapters for approved predictive data sources."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .models import PredictiveContext

PREDICTIVE_SOURCES = (
    "knowledge_evolution",
    "decision_evolution",
    "autonomous_learning_center",
    "intelligence_center",
    "business_intelligence_center",
    "performance_insights",
    "analytics_center",
    "operations_planner",
    "risk_control",
)


class ReadOnlyPredictiveSource(Protocol):
    def read_history(
        self,
        start: datetime,
        end: datetime,
        context: PredictiveContext,
        *,
        limit: int,
    ) -> tuple[dict[str, object], ...]: ...


class ReferenceOnlyPredictiveSource:
    """Returns bounded mock references and exposes no mutation methods."""

    def __init__(self, source: str, service: object | None = None) -> None:
        if source not in PREDICTIVE_SOURCES:
            raise ValueError(f"Unsupported predictive source: {source}")
        self.source = source
        self.service = service

    def read_history(
        self,
        start: datetime,
        end: datetime,
        context: PredictiveContext,
        *,
        limit: int,
    ) -> tuple[dict[str, object], ...]:
        if start >= end:
            raise ValueError("A valid bounded historical range is required.")
        if not 1 <= limit <= 1_000:
            raise ValueError("Result limit must be within [1, 1000].")
        return (
            {
                "source": self.source,
                "tenant": context.tenant,
                "workspace": context.workspace,
                "reference": f"{self.source}://history/{start.date().isoformat()}",
                "integrity_reference": (
                    f"integrity://{self.source}/{end.date().isoformat()}"
                ),
                "read_only": True,
                "reference_only": True,
                "execution": False,
                "publishing": False,
                "configuration_change": False,
                "restriction_bypass": False,
            },
        )
