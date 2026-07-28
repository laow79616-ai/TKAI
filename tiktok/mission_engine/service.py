"""Approval-gated coordinator for autonomous TikTok missions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .adapters import INTEGRATION_MODULES, MissionModulePort, ReferenceOnlyPort
from .metrics import MissionMetrics
from .models import (
    ApprovalState,
    AuditEntry,
    Checkpoint,
    Mission,
    MissionScope,
    MissionState,
    RiskState,
    utcnow,
)


class TikTokAutonomousMissionEngine:
    """Coordinates existing modules without performing platform execution."""

    def __init__(self, modules: Mapping[str, MissionModulePort] | None = None) -> None:
        supplied = modules or {}
        self.modules = {
            name: supplied.get(name, ReferenceOnlyPort(name))
            for name in INTEGRATION_MODULES
        }
        self.missions: dict[str, Mission] = {}
        self.checkpoints: dict[str, list[Checkpoint]] = {}
        self.audit: list[AuditEntry] = []
        self.metrics = MissionMetrics()

    @staticmethod
    def _require(scope: MissionScope, action: str) -> None:
        required = f"tiktok:mission-engine:{action}"
        if (
            required not in scope.permissions
            and "tiktok:mission-engine:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(mission: Mission, scope: MissionScope) -> None:
        if mission.tenant != scope.tenant or mission.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _mission(self, reference: str, scope: MissionScope) -> Mission:
        mission = self.missions[reference]
        self._scoped(mission, scope)
        return mission

    def _record(self, mission: Mission, scope: MissionScope, action: str) -> None:
        self.audit.append(
            AuditEntry(
                mission.id, mission.tenant, mission.workspace, scope.actor, action
            )
        )

    def scoped_missions(self, scope: MissionScope) -> list[Mission]:
        self._require(scope, "read")
        return [
            item
            for item in self.missions.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def enqueue(self, mission: Mission, scope: MissionScope) -> Mission:
        self._require(scope, "write")
        self._scoped(mission, scope)
        mission.validate()
        if mission.id in self.missions:
            raise ValueError("Mission ID must be unique.")
        if mission.approval_state is not ApprovalState.APPROVED:
            raise PermissionError("Approved mission required.")
        if mission.risk_state is not RiskState.CLEAR:
            raise PermissionError("Clear mission risk state required.")
        self.missions[mission.id] = mission
        self.metrics.increment("tiktok_missions_total")
        self._record(mission, scope, "mission.queued")
        return mission

    def queue(self, scope: MissionScope) -> list[Mission]:
        missions = self.scoped_missions(scope)
        return sorted(
            missions,
            key=lambda item: (item.priority, item.created_at, item.id),
        )

    def _health(
        self, mission: Mission, scope: MissionScope
    ) -> dict[str, dict[str, object]]:
        health = {
            name: module.health(mission.id, scope)
            for name, module in self.modules.items()
        }
        if any(
            value.get("restriction_unresolved")
            or value.get("challenge_unresolved")
            for value in health.values()
        ):
            raise PermissionError(
                "Unresolved TikTok restriction or challenge stops the mission."
            )
        if any(not value.get("healthy", False) for value in health.values()):
            raise RuntimeError("Mission dependency health check failed.")
        return health

    def _dependencies_complete(self, mission: Mission, scope: MissionScope) -> bool:
        for reference in mission.dependencies:
            dependency = self._mission(reference, scope)
            if dependency.state is not MissionState.COMPLETED:
                return False
        return True

    def dispatch(
        self,
        reference: str,
        scope: MissionScope,
        *,
        worker: str,
        queue: str = "default",
    ) -> Mission:
        self._require(scope, "dispatch")
        mission = self._mission(reference, scope)
        if mission.state is not MissionState.QUEUED:
            raise ValueError("Only queued missions may be dispatched.")
        if mission.approval_state is not ApprovalState.APPROVED:
            raise PermissionError("Mission approval is no longer valid.")
        if mission.risk_state is not RiskState.CLEAR:
            raise PermissionError("Mission risk state blocks dispatch.")
        if not mission.execution_window.contains(utcnow()):
            raise PermissionError("Mission is outside its execution window.")
        if not self._dependencies_complete(mission, scope):
            raise RuntimeError("Mission dependencies are incomplete.")
        if not worker or not queue:
            raise ValueError("Worker selection and queue assignment are required.")
        self._health(mission, scope)
        mission.state = MissionState.DISPATCHING
        mission.worker = worker
        mission.queue = queue
        mission.attempts += 1
        mission.started_at = utcnow()
        mission.delegated = {
            name: module.dispatch(mission, scope)
            for name, module in self.modules.items()
            if name not in {"autonomous_operation", "risk_control"}
        }
        mission.state = MissionState.RUNNING
        self.metrics.set(
            "tiktok_missions_running",
            sum(
                item.state is MissionState.RUNNING
                for item in self.scoped_missions(scope)
            ),
        )
        self._record(mission, scope, "mission.dispatched")
        return mission

    def checkpoint(
        self,
        reference: str,
        checkpoint_reference: str,
        progress: float,
        scope: MissionScope
    ) -> Checkpoint:
        self._require(scope, "write")
        mission = self._mission(reference, scope)
        if mission.state not in {MissionState.RUNNING, MissionState.RECOVERING}:
            raise ValueError("Only active missions accept checkpoints.")
        if not checkpoint_reference or not 0 <= progress <= 1:
            raise ValueError("Checkpoint reference and bounded progress are required.")
        checkpoint = Checkpoint(
            mission.id,
            mission.tenant,
            mission.workspace,
            checkpoint_reference,
            progress,
        )
        self.checkpoints.setdefault(mission.id, []).append(checkpoint)
        mission.checkpoint = checkpoint_reference
        self._record(mission, scope, "mission.checkpoint")
        return checkpoint

    def complete(self, reference: str, scope: MissionScope) -> Mission:
        self._require(scope, "write")
        mission = self._mission(reference, scope)
        if mission.state is not MissionState.RUNNING:
            raise ValueError("Only running missions may complete.")
        mission.state = MissionState.COMPLETED
        mission.finished_at = utcnow()
        self.metrics.increment("tiktok_missions_completed")
        self._update_terminal_metrics(mission, scope)
        self._record(mission, scope, "mission.completed")
        return mission

    def fail(self, reference: str, reason: str, scope: MissionScope) -> Mission:
        self._require(scope, "write")
        mission = self._mission(reference, scope)
        if not reason:
            raise ValueError("A non-secret failure reason is required.")
        mission.state = MissionState.FAILED
        mission.failure = reason
        mission.finished_at = utcnow()
        self.metrics.increment("tiktok_missions_failed")
        self._update_terminal_metrics(mission, scope)
        self._record(mission, scope, "mission.failed")
        return mission

    def _update_terminal_metrics(
        self, mission: Mission, scope: MissionScope
    ) -> None:
        self.metrics.set(
            "tiktok_missions_running",
            sum(
                item.state is MissionState.RUNNING
                for item in self.scoped_missions(scope)
            ),
        )
        if mission.started_at and mission.finished_at:
            latency = (mission.finished_at - mission.started_at).total_seconds()
            self.metrics.set("tiktok_mission_latency_seconds", max(0.0, latency))

    def recover(
        self, reference: str, scope: MissionScope, *, rollback: bool = False
    ) -> Mission:
        self._require(scope, "recover")
        mission = self._mission(reference, scope)
        if mission.state not in {
            MissionState.FAILED,
            MissionState.PAUSED,
            MissionState.RECOVERING,
        }:
            raise ValueError("Only failed, paused, or recovering missions may recover.")
        self._health(mission, scope)
        mission.state = MissionState.RECOVERING
        if rollback:
            for module in self.modules.values():
                module.rollback(mission.id, scope)
            mission.state = MissionState.ROLLED_BACK
            self._record(mission, scope, "mission.rolled_back")
            return mission
        if mission.attempts >= mission.max_attempts:
            raise RuntimeError("Mission retry limit reached.")
        if mission.checkpoint:
            mission.delegated = {
                name: module.resume(mission.id, mission.checkpoint, scope)
                for name, module in self.modules.items()
                if name not in {"autonomous_operation", "risk_control"}
            }
        else:
            mission.delegated = {
                name: module.recover(mission.id, scope)
                for name, module in self.modules.items()
                if name not in {"autonomous_operation", "risk_control"}
            }
        mission.attempts += 1
        mission.failure = None
        mission.finished_at = None
        mission.state = MissionState.RUNNING
        self.metrics.increment("tiktok_missions_recovered")
        self.metrics.set(
            "tiktok_missions_running",
            sum(
                item.state is MissionState.RUNNING
                for item in self.scoped_missions(scope)
            ),
        )
        self._record(mission, scope, "mission.recovered")
        return mission

    def health(self, reference: str, scope: MissionScope) -> dict[str, Any]:
        self._require(scope, "read")
        mission = self._mission(reference, scope)
        modules = {
            name: module.health(mission.id, scope)
            for name, module in self.modules.items()
        }
        groups = {
            "runtime_health": ("runtime_manager", "browser_cluster", "device_center"),
            "execution_health": (
                "task_scheduler",
                "automation_engine",
                "workflow_center",
                "execution_engine",
            ),
            "resource_health": ("resource_center",),
            "recovery_health": ("runtime_manager", "risk_control"),
        }
        return {
            "mission_health": mission.state.value,
            **{
                group: all(
                    bool(modules[name].get("healthy", False))
                    for name in names
                )
                for group, names in groups.items()
            },
            "modules": modules,
        }

    def analytics(self, scope: MissionScope) -> dict[str, float]:
        missions = self.scoped_missions(scope)
        states = tuple(item.state for item in missions)
        return {
            "total": float(len(missions)),
            "queued": float(states.count(MissionState.QUEUED)),
            "running": float(states.count(MissionState.RUNNING)),
            "completed": float(states.count(MissionState.COMPLETED)),
            "failed": float(states.count(MissionState.FAILED)),
            "recovered": self.metrics.values["tiktok_missions_recovered"],
        }

    def dashboard(self, scope: MissionScope) -> dict[str, Any]:
        missions = self.queue(scope)
        return {
            "sections": [
                "mission_queue",
                "mission_health",
                "dispatch",
                "recovery",
                "analytics",
            ],
            "mission_queue": [item.to_dict() for item in missions],
            "mission_health": {
                item.id: self.health(item.id, scope) for item in missions
            },
            "dispatch": [
                {"mission_id": item.id, "worker": item.worker, "queue": item.queue}
                for item in missions
                if item.worker
            ],
            "recovery": [
                item.to_dict()
                for item in missions
                if item.state
                in {MissionState.RECOVERING, MissionState.ROLLED_BACK}
            ],
            "analytics": self.analytics(scope),
        }

    def audit_entries(self, scope: MissionScope) -> Iterable[AuditEntry]:
        self._require(scope, "read")
        return (
            item
            for item in self.audit
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        )
