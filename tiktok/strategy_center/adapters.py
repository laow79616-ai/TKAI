"""Read-only inputs and reference-only handoff ports."""

from __future__ import annotations

from typing import Any, Protocol

from .models import StrategyHandoff, StrategyScope

INPUT_MODULES = (
    "business_intelligence",
    "performance_insights",
    "growth_center",
    "campaign_center",
    "creator_workspace",
    "content_pipeline",
    "control_tower",
    "decision_center",
    "optimization_center",
    "operations_planner",
    "autonomous_operation",
    "mission_engine",
    "recovery_center",
    "risk_control",
    "runtime_manager",
    "resource_center",
    "task_scheduler",
)

HANDOFF_MODULES = (
    "operations_planner",
    "decision_center",
    "optimization_center",
    "autonomous_operation",
    "mission_engine",
    "campaign_center",
    "creator_workspace",
    "content_pipeline",
    "workflow_center",
)


class StrategyInputPort(Protocol):
    @property
    def read_only(self) -> bool: ...
    def snapshot(self, scope: StrategyScope) -> dict[str, Any]: ...


class StrategyHandoffPort(Protocol):
    def accept_reference(
        self, handoff: StrategyHandoff, scope: StrategyScope
    ) -> str: ...


class NullStrategyInputPort:
    read_only = True

    def snapshot(self, scope: StrategyScope) -> dict[str, Any]:
        return {
            "status": "unavailable",
            "health": 0.5,
            "capacity": 0.5,
            "risk": 0.25,
            "source": "bounded-test-double",
        }


class NullStrategyHandoffPort:
    def accept_reference(self, handoff: StrategyHandoff, scope: StrategyScope) -> str:
        return f"reference-only://{handoff.target.value}/{handoff.id}"


class ExistingModuleInputAdapter:
    """Reads only an existing module's dashboard/analytics surface."""

    read_only = True

    def __init__(self, module: Any) -> None:
        self.module = module

    def snapshot(self, scope: StrategyScope) -> dict[str, Any]:
        for method_name in ("strategy_snapshot", "analytics", "dashboard", "health"):
            method = getattr(self.module, method_name, None)
            if callable(method):
                try:
                    value = method(scope)
                except (TypeError, AttributeError):
                    continue
                if isinstance(value, dict):
                    return dict(value)
        return {
            "status": "available",
            "health": 0.75,
            "capacity": 0.5,
            "risk": 0.25,
            "source": type(self.module).__name__,
        }
