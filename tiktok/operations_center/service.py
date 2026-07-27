"""Tenant-isolated monitoring and approved control plane for TikTok operations."""

from __future__ import annotations

from dataclasses import asdict
from time import perf_counter
from typing import Any

from .adapters import MODULES, NullOperationsModulePort, OperationsModulePort
from .metrics import OperationsMetrics
from .models import (
    HIGH_RISK_ACTIONS,
    ActionKind,
    ActivityEntry,
    AlertStatus,
    Approval,
    AuditRecord,
    HealthSnapshot,
    IncidentStatus,
    OperationsAlert,
    OperationsCenter,
    OperationsIncident,
    OperationsScope,
    OperationsStatus,
    OperationsTask,
    RecoveryRequest,
    TaskStatus,
    utcnow,
)


class TikTokOperationsCommandCenter:
    """Unifies status and bounded actions without bypass or evasion behavior."""

    def __init__(self, ports: dict[str, OperationsModulePort] | None = None) -> None:
        null = NullOperationsModulePort()
        self.ports = {name: (ports or {}).get(name, null) for name in MODULES}
        self.centers: dict[str, OperationsCenter] = {}
        self.tasks: dict[str, OperationsTask] = {}
        self.alerts: dict[str, OperationsAlert] = {}
        self.incidents: dict[str, OperationsIncident] = {}
        self.recoveries: dict[str, RecoveryRequest] = {}
        self.approvals: dict[str, Approval] = {}
        self.activity: list[ActivityEntry] = []
        self.audit: list[AuditRecord] = []
        self.kill_switches: set[tuple[str, str]] = set()
        self.metrics = OperationsMetrics()

    @staticmethod
    def _require(scope: OperationsScope, permission: str) -> None:
        required = f"tiktok:operations:{permission}"
        if (
            required not in scope.permissions
            and "tiktok:operations:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: Any, scope: OperationsScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    @staticmethod
    def _safe_audit_text(value: str) -> None:
        lowered = value.casefold()
        forbidden = ("password=", "secret=", "token=", "cookie=", "session=")
        if any(marker in lowered for marker in forbidden):
            raise ValueError("Secrets are forbidden in activity and audit records.")

    def _record(
        self,
        scope: OperationsScope,
        action: str,
        resource: str,
        reason: str,
        correlation_id: str,
        approval_reference: str = "",
    ) -> None:
        self._safe_audit_text(reason)
        self.audit.append(
            AuditRecord(
                scope.actor,
                action,
                resource,
                scope.tenant,
                scope.workspace,
                reason,
                approval_reference=approval_reference,
                correlation_id=correlation_id,
            )
        )
        self.activity.append(
            ActivityEntry(
                scope.tenant,
                scope.workspace,
                "user" if scope.actor != "system" else "system",
                f"{action}: {resource}",
                scope.actor,
                correlation_id,
            )
        )

    def create_center(
        self, center: OperationsCenter, scope: OperationsScope
    ) -> OperationsCenter:
        self._require(scope, "write")
        self._scoped(center, scope)
        center.validate()
        if center.id in self.centers:
            raise ValueError("Operations center ID must be unique.")
        self.centers[center.id] = center
        self.metrics.increment("tiktok_operations_centers_total")
        self._record(scope, "center.created", center.id, "create", center.id)
        return center

    def transition(
        self,
        reference: str,
        status: OperationsStatus,
        scope: OperationsScope,
    ) -> OperationsCenter:
        self._require(scope, "write")
        center = self.centers[reference]
        self._scoped(center, scope)
        allowed = {
            OperationsStatus.DRAFT: {
                OperationsStatus.ACTIVE,
                OperationsStatus.ARCHIVED,
            },
            OperationsStatus.ACTIVE: {
                OperationsStatus.MAINTENANCE,
                OperationsStatus.PAUSED,
                OperationsStatus.RECOVERING,
            },
            OperationsStatus.MAINTENANCE: {
                OperationsStatus.ACTIVE,
                OperationsStatus.PAUSED,
            },
            OperationsStatus.PAUSED: {
                OperationsStatus.ACTIVE,
                OperationsStatus.RECOVERING,
                OperationsStatus.ARCHIVED,
            },
            OperationsStatus.RECOVERING: {
                OperationsStatus.ACTIVE,
                OperationsStatus.PAUSED,
            },
            OperationsStatus.ARCHIVED: {
                OperationsStatus.DRAFT,
                OperationsStatus.DELETED,
            },
            OperationsStatus.DELETED: set(),
        }
        if status not in allowed[center.status]:
            current = center.status.value
            transition = f"{current} -> {status.value}"
            raise ValueError(f"Invalid operations transition: {transition}")
        center.status, center.version = status, center.version + 1
        self._record(scope, "center.transition", reference, status.value, reference)
        return center

    def scoped_values(self, values: Any, scope: OperationsScope) -> list[Any]:
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def register_task(
        self, task: OperationsTask, scope: OperationsScope
    ) -> OperationsTask:
        self._require(scope, "write")
        self._scoped(task, scope)
        task.validate()
        self.tasks[task.id] = task
        self.metrics.set(
            "tiktok_operations_active_tasks_total",
            len(
                [
                    item
                    for item in self.scoped_values(self.tasks.values(), scope)
                    if item.status in {TaskStatus.QUEUED, TaskStatus.RUNNING}
                ]
            ),
        )
        self._record(scope, "task.registered", task.id, task.kind, task.id)
        return task

    def raise_alert(
        self, alert: OperationsAlert, scope: OperationsScope
    ) -> OperationsAlert:
        self._require(scope, "write")
        self._scoped(alert, scope)
        self.alerts[alert.id] = alert
        self.metrics.increment("tiktok_operations_alerts_total")
        self._record(scope, "alert.opened", alert.id, alert.message, alert.id)
        return alert

    def open_incident(
        self, incident: OperationsIncident, scope: OperationsScope
    ) -> OperationsIncident:
        self._require(scope, "write")
        self._scoped(incident, scope)
        self.incidents[incident.id] = incident
        self.metrics.increment("tiktok_operations_incidents_total")
        self._record(scope, "incident.opened", incident.id, incident.title, incident.id)
        return incident

    def approve(self, approval: Approval, scope: OperationsScope) -> Approval:
        self._require(scope, "approve")
        self._scoped(approval, scope)
        if approval.expires_at <= utcnow():
            raise ValueError("Approval expiration must be in the future.")
        self.approvals[approval.id] = approval
        self._record(
            scope,
            "approval.granted",
            approval.resource_reference,
            approval.action.value,
            approval.id,
        )
        return approval

    def _approval_for(
        self, action: ActionKind, resource: str, scope: OperationsScope
    ) -> Approval:
        matches = [
            item
            for item in self.approvals.values()
            if item.action is action
            and item.resource_reference == resource
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.expires_at > utcnow()
        ]
        if not matches:
            raise PermissionError("Valid high-risk action approval required.")
        return matches[-1]

    def execute_action(
        self,
        action: ActionKind,
        resource_reference: str,
        module: str,
        reason: str,
        correlation_id: str,
        scope: OperationsScope,
    ) -> dict[str, Any]:
        started = perf_counter()
        self._require(scope, "control")
        self._safe_audit_text(reason)
        if module not in self.ports:
            raise ValueError("Action target must be an approved TikTok module.")
        approval = (
            self._approval_for(action, resource_reference, scope)
            if action in HIGH_RISK_ACTIONS
            else None
        )
        if (scope.tenant, scope.workspace) in self.kill_switches and action not in {
            ActionKind.TRIGGER_HEALTH_CHECK,
            ActionKind.OPEN_INCIDENT,
        }:
            raise PermissionError("Workspace kill switch is active.")
        try:
            result = self.ports[module].execute(action.value, resource_reference, scope)
            if action is ActionKind.KILL_SWITCH:
                self.kill_switches.add((scope.tenant, scope.workspace))
            self.metrics.increment("tiktok_operations_actions_total")
            self._record(
                scope,
                f"action.{action.value}",
                resource_reference,
                reason,
                correlation_id,
                approval.id if approval else "",
            )
            return result
        except Exception:
            self.metrics.increment("tiktok_operations_action_failures_total")
            raise
        finally:
            self.metrics.set(
                "tiktok_operations_latency_seconds", perf_counter() - started
            )

    def health(self, scope: OperationsScope) -> HealthSnapshot:
        self._require(scope, "read")
        scores: dict[str, float] = {}
        for name, port in self.ports.items():
            value = port.status(scope)
            healthy = float(value.get("healthy", 0))
            unhealthy = float(value.get("unhealthy", 0))
            scores[name] = (
                healthy / (healthy + unhealthy) * 100 if healthy + unhealthy else 0
            )
        composite = sum(scores.values()) / len(scores)
        self.metrics.set("tiktok_operations_health_score", composite)
        return HealthSnapshot(scope.tenant, scope.workspace, scores, composite)

    def recover(
        self, request: RecoveryRequest, scope: OperationsScope
    ) -> RecoveryRequest:
        self._require(scope, "recover")
        self._scoped(request, scope)
        request.validate()
        if request.restriction_active or request.challenge_unresolved:
            request.outcome = "stopped_restriction_or_challenge"
            self.recoveries[request.id] = request
            self._record(
                scope,
                "recovery.stopped",
                request.resource_reference,
                request.outcome,
                request.id,
            )
            return request
        if request.manual_approval:
            self._approval_for(
                ActionKind.RETRY_APPROVED_JOB, request.resource_reference, scope
            )
        request.attempts += 1
        request.outcome = (
            "maximum_attempts_reached"
            if request.attempts >= request.maximum_attempts
            else "accepted"
        )
        self.recoveries[request.id] = request
        self.metrics.increment("tiktok_operations_recoveries_total")
        if request.outcome == "accepted":
            self.metrics.increment("tiktok_operations_recovery_success_total")
        self._record(
            scope,
            "recovery.requested",
            request.resource_reference,
            request.outcome,
            request.id,
        )
        return request

    def overview(self, scope: OperationsScope) -> dict[str, Any]:
        self._require(scope, "read")
        statuses = {name: port.status(scope) for name, port in self.ports.items()}
        tasks = self.scoped_values(self.tasks.values(), scope)
        alerts = self.scoped_values(self.alerts.values(), scope)
        incidents = self.scoped_values(self.incidents.values(), scope)

        def count(module: str, key: str) -> int:
            return int(statuses[module].get(key, 0))

        return {
            "total_accounts": count("accounts", "total"),
            "active_accounts": count("accounts", "active"),
            "paused_accounts": count("accounts", "paused"),
            "restricted_accounts": count("accounts", "restricted"),
            "active_browsers": count("browsers", "active"),
            "browser_failures": count("browsers", "failures"),
            "healthy_proxies": count("proxies", "healthy"),
            "unhealthy_proxies": count("proxies", "unhealthy"),
            "running_workflows": count("workflows", "running"),
            "queued_tasks": sum(item.status is TaskStatus.QUEUED for item in tasks),
            "publishing_jobs": count("publishing", "jobs"),
            "collection_jobs": count("collection", "jobs"),
            "interaction_tasks": count("interaction", "tasks"),
            "risk_alerts": sum(item.status is AlertStatus.OPEN for item in alerts),
            "open_incidents": sum(
                item.status is not IncidentStatus.CLOSED for item in incidents
            ),
            "unified_status": {
                f"{name}_status": value.get("status", "unknown")
                for name, value in statuses.items()
            },
        }

    def dashboard(self, scope: OperationsScope) -> dict[str, Any]:
        return {
            "sections": (
                "Operations Overview",
                "Accounts",
                "Browsers",
                "Proxies",
                "Farming",
                "Content",
                "Publishing",
                "Collection",
                "Interaction",
                "Risk",
                "Workflows",
                "Tasks",
                "Alerts",
                "Incidents",
                "Health",
                "Recovery",
                "Activity",
                "Audit",
            ),
            "overview": self.overview(scope),
            "health": asdict(self.health(scope)),
        }
