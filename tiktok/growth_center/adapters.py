"""Read-only ports for existing bounded TikTok centers."""

from __future__ import annotations

from typing import Any, Protocol

from .models import RequestScope

INTEGRATION_MODULES = (
    "content_pipeline",
    "campaign_center",
    "creator_workspace",
    "analytics_center",
    "intelligent_decision_center",
    "optimization_center",
    "operations_planner",
    "control_tower",
)


class ReadOnlyGrowthInputPort(Protocol):
    def snapshot(self, module: str, scope: RequestScope) -> dict[str, Any]: ...


class ProposalPort(Protocol):
    def propose(self, recommendation_id: str, scope: RequestScope) -> str: ...


class BoundedTestDouble:
    """Offline test adapter; exposes observations and proposal receipts only."""

    def __init__(self) -> None:
        self.proposals: list[str] = []

    def snapshot(self, module: str, scope: RequestScope) -> dict[str, Any]:
        if module not in INTEGRATION_MODULES:
            raise ValueError("Unknown bounded integration module.")
        return {"module": module, "score": 0.75, "read_only": True}

    def propose(self, recommendation_id: str, scope: RequestScope) -> str:
        self.proposals.append(recommendation_id)
        return f"ref://growth-proposal/{recommendation_id}"
