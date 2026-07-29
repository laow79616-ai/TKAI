"""Bounded ports to completed TikTok modules; no execution is implemented here."""

from __future__ import annotations

from typing import Any, Protocol

from .models import Mission, MissionScope

INTEGRATION_MODULES = (
    "autonomous_operation",
    "task_scheduler",
    "automation_engine",
    "workflow_center",
    "execution_engine",
    "runtime_manager",
    "resource_center",
    "browser_cluster",
    "device_center",
    "risk_control",
)


class MissionModulePort(Protocol):
    def health(self, mission_id: str, scope: MissionScope) -> dict[str, object]: ...

    def dispatch(self, mission: Mission, scope: MissionScope) -> str: ...

    def resume(self, mission_id: str, checkpoint: str, scope: MissionScope) -> str: ...

    def rollback(self, mission_id: str, scope: MissionScope) -> None: ...

    def recover(self, mission_id: str, scope: MissionScope) -> str: ...


class ReferenceOnlyPort:
    """Offline-safe reference adapter used by tests and unbound composition."""

    def __init__(self, module: str) -> None:
        self.module = module

    def health(self, mission_id: str, scope: MissionScope) -> dict[str, object]:
        return {
            "healthy": True,
            "restriction_unresolved": False,
            "challenge_unresolved": False,
        }

    def dispatch(self, mission: Mission, scope: MissionScope) -> str:
        return f"{self.module}://{mission.id}/delegated"

    def resume(self, mission_id: str, checkpoint: str, scope: MissionScope) -> str:
        return f"{self.module}://{mission_id}/resume/{checkpoint}"

    def rollback(self, mission_id: str, scope: MissionScope) -> None:
        return None

    def recover(self, mission_id: str, scope: MissionScope) -> str:
        return f"{self.module}://{mission_id}/recovery"


class ExistingModulePort(ReferenceOnlyPort):
    """Adapter around an existing service; methods never expose secrets or bypasses."""

    def __init__(self, module: str, service: Any) -> None:
        super().__init__(module)
        self.service = service

    def health(self, mission_id: str, scope: MissionScope) -> dict[str, object]:
        restrictions = getattr(self.service, "restrictions", {})
        unresolved = any(
            not bool(getattr(item, "resolved", False))
            for item in getattr(restrictions, "values", lambda: ())()
        )
        return {
            "healthy": not unresolved,
            "restriction_unresolved": unresolved,
            "challenge_unresolved": False,
        }
