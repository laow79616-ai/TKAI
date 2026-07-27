"""Tenant-scoped Enterprise AI Operations Platform domain services."""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .metrics import OperationsMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class OperationsScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"operations:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class OperationsCenter:
    id: str
    name: str
    description: str
    owner: str
    tenant: str
    workspace: str
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HealthRecord:
    component: str
    component_id: str
    status: HealthStatus
    tenant: str
    workspace: str
    checked_at: datetime
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["checked_at"] = self.checked_at.isoformat()
        return value


@dataclass(slots=True)
class OperationsJob:
    id: str
    kind: str
    tenant: str
    workspace: str
    status: JobStatus = JobStatus.PENDING
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["created_at"] = self.created_at.isoformat()
        return value


@dataclass(slots=True)
class MaintenanceWindow:
    id: str
    tenant: str
    workspace: str
    starts_at: datetime
    ends_at: datetime
    action: str
    status: str = "scheduled"
    approval_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["starts_at"] = self.starts_at.isoformat()
        value["ends_at"] = self.ends_at.isoformat()
        return value


@dataclass(slots=True)
class BackupRecord:
    id: str
    tenant: str
    workspace: str
    categories: tuple[str, ...]
    schedule: str | None
    retention_days: int
    status: str = "completed"
    created_at: datetime = field(default_factory=utcnow)
    checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["created_at"] = self.created_at.isoformat()
        return value


@dataclass(slots=True)
class CapacitySnapshot:
    tenant: str
    workspace: str
    cpu: float
    memory: float
    storage: float
    token_usage: int
    queue: int
    concurrency: int
    forecast: dict[str, float]
    recorded_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["recorded_at"] = self.recorded_at.isoformat()
        return value


@dataclass(slots=True)
class OperationsEvent:
    id: str
    event_type: str
    severity: Severity
    source: str
    tenant: str
    workspace: str
    lifecycle: str
    occurred_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["severity"] = self.severity.value
        value["occurred_at"] = self.occurred_at.isoformat()
        return value


@dataclass(slots=True)
class Notification:
    id: str
    channel: str
    destination: str
    tenant: str
    workspace: str
    status: str = "pending"
    attempts: int = 0
    escalation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["destination"] = "[REDACTED]"
        return value


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    outcome: str
    occurred_at: datetime
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["occurred_at"] = self.occurred_at.isoformat()
        return value


class OperationsPlatform:
    """In-memory reference service with isolation, RBAC, audit and approvals."""

    HEALTH_COMPONENTS = frozenset(
        {
            "application",
            "agent",
            "workflow",
            "model",
            "knowledge",
            "plugin",
            "infrastructure",
        }
    )
    BACKUP_CATEGORIES = frozenset(
        {"configuration", "metadata", "knowledge", "workflow", "application", "policy"}
    )
    AUTOMATION_KINDS = frozenset(
        {"scheduled", "maintenance", "cleanup", "optimization", "rotation", "repair"}
    )
    MAINTENANCE_ACTIONS = frozenset({"drain", "pause", "resume", "upgrade", "rollback"})
    SECRET_PATTERN = re.compile(
        r"(?i)(password|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;]+"
    )

    def __init__(self) -> None:
        self.centers: dict[str, OperationsCenter] = {}
        self.health_records: list[HealthRecord] = []
        self.maintenance_windows: dict[str, MaintenanceWindow] = {}
        self.backups: dict[str, BackupRecord] = {}
        self.jobs: dict[str, OperationsJob] = {}
        self.capacity_snapshots: list[CapacitySnapshot] = []
        self.automations: dict[str, OperationsJob] = {}
        self.diagnostics: dict[str, OperationsJob] = {}
        self.logs: list[dict[str, Any]] = []
        self.events: list[OperationsEvent] = []
        self.notifications: dict[str, Notification] = {}
        self.audit: list[AuditEntry] = []
        self.metrics = OperationsMetrics()

    @staticmethod
    def _check(record: Any, scope: OperationsScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope operations access denied.")

    @staticmethod
    def _require(scope: OperationsScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "operations:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: OperationsScope, **metadata: Any) -> None:
        self.audit.append(
            AuditEntry(
                action,
                scope.actor,
                scope.tenant,
                scope.workspace,
                "success",
                utcnow(),
                metadata,
            )
        )

    def _scoped(self, values: Any, scope: OperationsScope) -> list[Any]:
        self._require(scope, "operations:read")
        return [
            value
            for value in values
            if value.tenant == scope.tenant and value.workspace == scope.workspace
        ]

    def create_center(
        self, center: OperationsCenter, scope: OperationsScope
    ) -> OperationsCenter:
        self._require(scope, "operations:write")
        self._check(center, scope)
        if center.id in self.centers:
            raise ValueError("Operations center already exists.")
        self.centers[center.id] = center
        self._audit("operations.center.create", scope, center_id=center.id)
        return center

    def list_centers(self, scope: OperationsScope) -> list[OperationsCenter]:
        return self._scoped(self.centers.values(), scope)

    def check_health(
        self,
        component: str,
        component_id: str,
        status: HealthStatus,
        scope: OperationsScope,
        details: dict[str, Any] | None = None,
    ) -> HealthRecord:
        self._require(scope, "operations:execute")
        if component not in self.HEALTH_COMPONENTS:
            raise ValueError("Unsupported health component.")
        record = HealthRecord(
            component,
            component_id,
            status,
            scope.tenant,
            scope.workspace,
            utcnow(),
            details or {},
        )
        self.health_records.append(record)
        self.metrics.increment("health_checks_total")
        self._audit(
            "health.check", scope, component=component, component_id=component_id
        )
        return record

    def schedule_maintenance(
        self, window: MaintenanceWindow, scope: OperationsScope
    ) -> MaintenanceWindow:
        self._require(scope, "operations:write")
        self._check(window, scope)
        if window.action not in self.MAINTENANCE_ACTIONS:
            raise ValueError("Unsupported maintenance action.")
        if window.ends_at <= window.starts_at:
            raise ValueError("Maintenance window end must follow start.")
        if window.action in {"upgrade", "rollback"} and not window.approval_id:
            raise PermissionError("Approval is required for upgrade and rollback.")
        self.maintenance_windows[window.id] = window
        self._audit(
            "maintenance.schedule",
            scope,
            window_id=window.id,
            maintenance_action=window.action,
        )
        return window

    def create_backup(
        self,
        backup_id: str,
        categories: tuple[str, ...],
        scope: OperationsScope,
        schedule: str | None = None,
        retention_days: int = 30,
    ) -> BackupRecord:
        self._require(scope, "operations:execute")
        if not categories or not set(categories) <= self.BACKUP_CATEGORIES:
            raise ValueError("Invalid backup categories.")
        if retention_days <= 0:
            raise ValueError("Retention must be positive.")
        backup = BackupRecord(
            backup_id,
            scope.tenant,
            scope.workspace,
            categories,
            schedule,
            retention_days,
            checksum=secrets.token_hex(16),
        )
        self.backups[backup.id] = backup
        self.metrics.increment("backup_total")
        self._audit("backup.create", scope, backup_id=backup.id)
        return backup

    def restore(
        self,
        backup_id: str,
        scope: OperationsScope,
        *,
        preview: bool = False,
        approval_id: str | None = None,
    ) -> OperationsJob:
        self._require(scope, "operations:execute")
        backup = self.backups[backup_id]
        self._check(backup, scope)
        if backup.status != "completed" or not backup.checksum:
            raise ValueError("Backup validation failed.")
        if not preview and not approval_id:
            raise PermissionError("Approval is required for restore.")
        job = OperationsJob(
            secrets.token_hex(12),
            "restore-preview" if preview else "restore",
            scope.tenant,
            scope.workspace,
            JobStatus.SUCCEEDED,
            {"backup_id": backup_id, "approval_id": approval_id},
            result={
                "validation": "passed",
                "preview": preview,
                "rollback": "available",
                "verification": "passed",
            },
        )
        self.jobs[job.id] = job
        if not preview:
            self.metrics.increment("restore_total")
        self.metrics.increment("operations_jobs_total")
        self._audit("restore.run", scope, job_id=job.id, preview=preview)
        return job

    def record_capacity(
        self, snapshot: CapacitySnapshot, scope: OperationsScope
    ) -> CapacitySnapshot:
        self._require(scope, "operations:execute")
        self._check(snapshot, scope)
        for value in (snapshot.cpu, snapshot.memory, snapshot.storage):
            if not 0 <= value <= 100:
                raise ValueError("Capacity percentages must be between 0 and 100.")
        self.capacity_snapshots.append(snapshot)
        if (
            max(snapshot.cpu, snapshot.memory, snapshot.storage) >= 85
            or snapshot.queue > 100
        ):
            self.metrics.increment("capacity_alerts_total")
            self.record_event("capacity.alert", Severity.WARNING, "capacity", scope)
        return snapshot

    def schedule_automation(
        self,
        automation_id: str,
        kind: str,
        payload: dict[str, Any],
        scope: OperationsScope,
    ) -> OperationsJob:
        self._require(scope, "operations:write")
        if kind not in self.AUTOMATION_KINDS:
            raise ValueError("Unsupported automation kind.")
        job = OperationsJob(
            automation_id, kind, scope.tenant, scope.workspace, payload=payload
        )
        self.automations[job.id] = job
        self.metrics.increment("operations_jobs_total")
        self._audit(
            "automation.schedule", scope, automation_id=automation_id, kind=kind
        )
        return job

    def run_diagnostics(
        self, checks: tuple[str, ...], scope: OperationsScope
    ) -> OperationsJob:
        self._require(scope, "operations:execute")
        supported = {
            "health_checks",
            "dependency_graph",
            "configuration_validation",
            "performance_analysis",
            "root_cause_reference",
        }
        if not checks or not set(checks) <= supported:
            raise ValueError("Unsupported diagnostic check.")
        result = {check: "passed" for check in checks}
        job = OperationsJob(
            secrets.token_hex(12),
            "diagnostics",
            scope.tenant,
            scope.workspace,
            JobStatus.SUCCEEDED,
            {"checks": checks},
            result=result,
        )
        self.diagnostics[job.id] = job
        self.metrics.increment("diagnostic_runs_total")
        self.metrics.increment("operations_jobs_total")
        self._audit("diagnostics.run", scope, job_id=job.id)
        return job

    def add_log(
        self, message: str, source: str, correlation_id: str, scope: OperationsScope
    ) -> dict[str, Any]:
        self._require(scope, "operations:execute")
        sanitized = self.SECRET_PATTERN.sub(
            lambda match: f"{match.group(1)}=[REDACTED]", message
        )
        entry = {
            "message": sanitized,
            "source": source,
            "correlation_id": correlation_id,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            "occurred_at": utcnow().isoformat(),
        }
        self.logs.append(entry)
        return entry

    def query_logs(
        self,
        scope: OperationsScope,
        *,
        source: str | None = None,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        self._require(scope, "operations:read")
        return [
            entry
            for entry in self.logs
            if entry["tenant"] == scope.tenant
            and entry["workspace"] == scope.workspace
            and (source is None or entry["source"] == source)
            and (correlation_id is None or entry["correlation_id"] == correlation_id)
        ]

    def record_event(
        self,
        event_type: str,
        severity: Severity,
        source: str,
        scope: OperationsScope,
        lifecycle: str = "created",
        metadata: dict[str, Any] | None = None,
    ) -> OperationsEvent:
        event = OperationsEvent(
            secrets.token_hex(12),
            event_type,
            severity,
            source,
            scope.tenant,
            scope.workspace,
            lifecycle,
            metadata=metadata or {},
        )
        self.events.append(event)
        return event

    def notify(
        self,
        channel: str,
        destination: str,
        scope: OperationsScope,
        *,
        escalation: str | None = None,
        sender: Callable[[str], bool] | None = None,
        retries: int = 3,
    ) -> Notification:
        self._require(scope, "operations:execute")
        if channel not in {"email", "webhook", "message_queue"}:
            raise ValueError("Unsupported notification channel.")
        notification = Notification(
            secrets.token_hex(12),
            channel,
            destination,
            scope.tenant,
            scope.workspace,
            escalation=escalation,
        )
        for _ in range(max(1, retries)):
            notification.attempts += 1
            if sender is None or sender(destination):
                notification.status = "sent"
                break
        if notification.status != "sent":
            notification.status = "escalated" if escalation else "failed"
        self.notifications[notification.id] = notification
        self.metrics.increment("notifications_total")
        self._audit(
            "notification.send", scope, notification_id=notification.id, channel=channel
        )
        return notification

    def report(self, report_type: str, scope: OperationsScope) -> dict[str, Any]:
        self._require(scope, "operations:read")
        if report_type not in {
            "health",
            "capacity",
            "usage",
            "availability",
            "operations",
        }:
            raise ValueError("Unsupported report.")
        return {
            "type": report_type,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            "generated_at": utcnow().isoformat(),
            "health_checks": len(self._scoped(self.health_records, scope)),
            "backups": len(self._scoped(self.backups.values(), scope)),
            "jobs": len(self._scoped(self.jobs.values(), scope))
            + len(self._scoped(self.automations.values(), scope))
            + len(self._scoped(self.diagnostics.values(), scope)),
        }

    def dashboard(self, scope: OperationsScope) -> dict[str, Any]:
        self._require(scope, "operations:read")
        return {
            "operations": [item.to_dict() for item in self.list_centers(scope)],
            "health": [
                item.to_dict() for item in self._scoped(self.health_records, scope)
            ],
            "backups": [
                item.to_dict() for item in self._scoped(self.backups.values(), scope)
            ],
            "capacity": [
                item.to_dict() for item in self._scoped(self.capacity_snapshots, scope)
            ],
            "automation": [
                item.to_dict()
                for item in self._scoped(self.automations.values(), scope)
            ],
            "diagnostics": [
                item.to_dict()
                for item in self._scoped(self.diagnostics.values(), scope)
            ],
            "events": [item.to_dict() for item in self._scoped(self.events, scope)],
            "notifications": [
                item.to_dict()
                for item in self._scoped(self.notifications.values(), scope)
            ],
            "reports": {
                name: self.report(name, scope)
                for name in (
                    "health",
                    "capacity",
                    "usage",
                    "availability",
                    "operations",
                )
            },
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAIOperationsPlatform = OperationsPlatform

__all__ = (
    "AuditEntry",
    "BackupRecord",
    "CapacitySnapshot",
    "EnterpriseAIOperationsPlatform",
    "HealthRecord",
    "HealthStatus",
    "JobStatus",
    "MaintenanceWindow",
    "Notification",
    "OperationsCenter",
    "OperationsEvent",
    "OperationsJob",
    "OperationsPlatform",
    "OperationsScope",
    "Severity",
    "utcnow",
)
