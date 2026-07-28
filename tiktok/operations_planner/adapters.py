"""Bounded read-only input and reference-only execution handoff ports."""

from __future__ import annotations

from typing import Any, Protocol

from .models import ExecutionHandoff, PlannerScope

INPUT_MODULES = (
    "accounts",
    "browsers",
    "devices",
    "proxies",
    "scheduler",
    "resources",
    "runtime",
    "automation",
    "workflow",
    "content",
    "publishing",
    "collection",
    "interaction",
    "risk",
    "analytics",
    "local_runtime",
)
HANDOFF_MODULES = ("automation", "workflow", "scheduler", "resources", "runtime")


class PlanningInputPort(Protocol):
    def snapshot(self, scope: PlannerScope) -> dict[str, Any]: ...


class ExecutionHandoffPort(Protocol):
    def accept(self, handoff: ExecutionHandoff, scope: PlannerScope) -> str: ...


class NullPlanningInputPort:
    def snapshot(self, scope: PlannerScope) -> dict[str, Any]:
        return {"status": "unavailable", "capacity": 0}


class NullExecutionHandoffPort:
    def accept(self, handoff: ExecutionHandoff, scope: PlannerScope) -> str:
        return f"reference-only://{handoff.id}"
