"""Ports that delegate work to completed TikTok modules."""

from __future__ import annotations

from typing import Any, Protocol

from .models import Mission, MissionPlan, OperationScope

DELEGATION_MODULES = (
    "task_scheduler",
    "automation_engine",
    "execution_engine",
    "workflow_center",
    "runtime_manager",
)


class MissionDelegationPort(Protocol):
    def dispatch(
        self, mission: Mission, plan: MissionPlan, scope: OperationScope
    ) -> str: ...

    def pause(self, mission_id: str, scope: OperationScope) -> None: ...

    def resume(
        self, mission_id: str, checkpoint: str, scope: OperationScope
    ) -> str: ...

    def rollback(
        self, mission_id: str, reference: str, scope: OperationScope
    ) -> None: ...

    def health(self, mission_id: str, scope: OperationScope) -> dict[str, object]: ...


class ReferenceOnlyPort:
    """Offline-safe adapter; production composition injects existing services."""

    def __init__(self, module: str) -> None:
        self.module = module

    def dispatch(
        self, mission: Mission, plan: MissionPlan, scope: OperationScope
    ) -> str:
        return f"{self.module}://{mission.id}/{plan.id}"

    def pause(self, mission_id: str, scope: OperationScope) -> None:
        return None

    def resume(
        self, mission_id: str, checkpoint: str, scope: OperationScope
    ) -> str:
        return f"{self.module}://{mission_id}/resume/{checkpoint}"

    def rollback(
        self, mission_id: str, reference: str, scope: OperationScope
    ) -> None:
        return None

    def health(self, mission_id: str, scope: OperationScope) -> dict[str, object]:
        return {
            "healthy": True,
            "restriction_unresolved": False,
            "challenge_unresolved": False,
            "resource_usage": 0.0,
            "queue_state": "ready",
        }


class ExistingModulePort(ReferenceOnlyPort):
    """Reference adapter bound to an existing module; it never executes work itself."""

    def __init__(self, module: str, service: Any) -> None:
        super().__init__(module)
        self.service = service

    def health(self, mission_id: str, scope: OperationScope) -> dict[str, object]:
        restrictions = getattr(self.service, "restrictions", {})
        instances = getattr(self.service, "instances", {})
        unresolved = any(
            getattr(item, "resolved", False) is False
            for item in getattr(restrictions, "values", lambda: ())()
        )
        unhealthy = any(
            str(getattr(item, "status", "healthy")).casefold()
            in {"failed", "unhealthy", "restricted"}
            for item in getattr(instances, "values", lambda: ())()
        )
        return {
            "healthy": not unhealthy,
            "restriction_unresolved": unresolved,
            "challenge_unresolved": False,
            "resource_usage": 0.0,
            "queue_state": "ready",
        }
