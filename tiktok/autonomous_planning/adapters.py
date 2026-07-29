"""Bounded read-only adapters for approved autonomous-planning inputs."""

from __future__ import annotations

from typing import Protocol

from .models import PlanningContext

PLANNING_SOURCES = (
    "autonomous_strategy",
    "mission_engine",
    "autonomous_operation",
    "governance_center",
    "intelligence_center",
    "autonomous_learning",
    "knowledge_evolution",
    "decision_evolution",
    "predictive_analytics",
    "operations_planner",
    "decision_center",
    "optimization_center",
    "recovery_resilience",
    "risk_control",
    "business_intelligence_center",
    "performance_insights",
    "analytics_center",
    "resource_center",
    "task_scheduler",
    "workflow_center",
    "operations_center",
)


class ReadOnlyPlanningSource(Protocol):
    def read_references(
        self, context: PlanningContext, *, limit: int
    ) -> tuple[dict[str, object], ...]: ...


class ReferenceOnlyPlanningSource:
    """Exposes reference reads only; deliberately has no mutation API."""

    def __init__(self, source: str) -> None:
        if source not in PLANNING_SOURCES:
            raise ValueError(f"Unsupported planning source: {source}")
        self.source = source

    def read_references(
        self, context: PlanningContext, *, limit: int
    ) -> tuple[dict[str, object], ...]:
        if not 1 <= limit <= 1_000:
            raise ValueError("Result limit must be within [1, 1000].")
        return (
            {
                "source": self.source,
                "tenant": context.tenant,
                "workspace": context.workspace,
                "reference": f"{self.source}://approved/default",
                "read_only": True,
                "reference_only": True,
                "execution": False,
                "runtime_mutation": False,
            },
        )
