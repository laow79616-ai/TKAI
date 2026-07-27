"""Secure, tenant-scoped Enterprise AI Command Center control plane."""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, TypeVar

from .metrics import CommandCenterMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CommandCenterStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Visibility(str, Enum):
    PRIVATE = "private"
    WORKSPACE = "workspace"
    TENANT = "tenant"
    GLOBAL = "global"


class ControlPlaneLevel(str, Enum):
    GLOBAL = "global"
    REGIONAL = "regional"
    TENANT = "tenant"
    WORKSPACE = "workspace"
    SERVICE = "service"
    AGENT = "agent"


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class IncidentPriority(str, Enum):
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"


class TaskType(str, Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"
    SCHEDULED = "scheduled"
    TRIGGERED = "triggered"


class ActivityType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    AUTOMATION = "automation"
    AUDIT = "audit"


class Scoped(Protocol):
    id: str
    tenant: str
    workspace: str


ScopedT = TypeVar("ScopedT", bound=Scoped)


@dataclass(frozen=True, slots=True)
class CommandCenterScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"command_center:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class CommandCenter:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    status: CommandCenterStatus = CommandCenterStatus.DRAFT
    visibility: Visibility = Visibility.PRIVATE
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ControlPlane:
    id: str
    tenant: str
    workspace: str
    name: str
    level: ControlPlaneLevel
    health: str = "unknown"
    synchronization: str = "pending"
    region: str | None = None
    target_reference: str | None = None


@dataclass(slots=True)
class Operation:
    id: str
    tenant: str
    workspace: str
    name: str
    kind: str
    status: ExecutionStatus = ExecutionStatus.QUEUED
    automation_status: str = "not_applicable"
    incident_status: str = "none"
    resource_usage: dict[str, float] = field(default_factory=dict)
    capacity: dict[str, float] = field(default_factory=dict)
    owner: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None


@dataclass(slots=True)
class Alert:
    id: str
    tenant: str
    workspace: str
    severity: AlertSeverity
    category: str
    source: str
    rule: str
    status: AlertStatus = AlertStatus.OPEN
    acknowledgement: str | None = None
    escalation: str | None = None
    resolution: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Incident:
    id: str
    tenant: str
    workspace: str
    title: str
    priority: IncidentPriority
    impact: str
    owner: str
    status: str = "open"
    root_cause_reference: str | None = None
    timeline: list[dict[str, Any]] = field(default_factory=list)
    resolution: str | None = None
    postmortem: str | None = None
    recovery: str | None = None


@dataclass(slots=True)
class Task:
    id: str
    tenant: str
    workspace: str
    name: str
    type: TaskType
    execution_status: ExecutionStatus = ExecutionStatus.QUEUED
    dependencies: tuple[str, ...] = ()
    retry_limit: int = 0
    retry_count: int = 0
    schedule: str | None = None
    trigger: str | None = None
    playbook_id: str | None = None


@dataclass(slots=True)
class Playbook:
    id: str
    tenant: str
    workspace: str
    name: str
    standard_operating_procedure: tuple[str, ...]
    automation_workflow_reference: str | None = None
    rollback_plan: tuple[str, ...] = ()
    approvals: tuple[str, ...] = ()
    execution_history: list[dict[str, Any]] = field(default_factory=list)
    version: str = "1.0.0"


@dataclass(slots=True)
class TopologyNode:
    id: str
    tenant: str
    workspace: str
    name: str
    kind: str
    dependencies: tuple[str, ...] = ()
    health: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HealthSnapshot:
    id: str
    tenant: str
    workspace: str
    target_id: str
    availability: float
    latency_seconds: float
    error_rate: float
    capacity: float
    resource_utilization: float
    trend: str = "stable"
    prediction_reference: str | None = None
    checked_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class ActivityEvent:
    id: str
    tenant: str
    workspace: str
    type: ActivityType
    actor: str
    action: str
    source: str
    occurred_at: datetime
    metadata: dict[str, Any]


class CommandCenterPlatform:
    """Operational command plane with isolation, RBAC, approvals and audit."""

    SECRET_KEY = re.compile(
        r"(?i)(password|secret|token|credential|api[_-]?key|authorization)"
    )
    ALLOWED_TRANSITIONS = {
        CommandCenterStatus.DRAFT: {
            CommandCenterStatus.ACTIVE,
            CommandCenterStatus.DELETED,
        },
        CommandCenterStatus.ACTIVE: {
            CommandCenterStatus.MAINTENANCE,
            CommandCenterStatus.PAUSED,
            CommandCenterStatus.ARCHIVED,
        },
        CommandCenterStatus.MAINTENANCE: {
            CommandCenterStatus.ACTIVE,
            CommandCenterStatus.PAUSED,
        },
        CommandCenterStatus.PAUSED: {
            CommandCenterStatus.ACTIVE,
            CommandCenterStatus.ARCHIVED,
        },
        CommandCenterStatus.ARCHIVED: {CommandCenterStatus.DELETED},
        CommandCenterStatus.DELETED: set(),
    }
    TOPOLOGY_KINDS = frozenset(
        {"service", "agent", "model", "pipeline", "infrastructure"}
    )

    def __init__(self) -> None:
        self.command_centers: dict[str, CommandCenter] = {}
        self.control_planes: dict[str, ControlPlane] = {}
        self.operations: dict[str, Operation] = {}
        self.alerts: dict[str, Alert] = {}
        self.incidents: dict[str, Incident] = {}
        self.tasks: dict[str, Task] = {}
        self.playbooks: dict[str, Playbook] = {}
        self.topology_nodes: dict[str, TopologyNode] = {}
        self.health_snapshots: dict[str, HealthSnapshot] = {}
        self.activity: list[ActivityEvent] = []
        self.metrics = CommandCenterMetrics()

    @staticmethod
    def _require(scope: CommandCenterScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "command_center:admin" not in scope.permissions
        ):
            raise PermissionError(f"Missing permission: {permission}")

    @staticmethod
    def _check(record: Scoped, scope: CommandCenterScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope Command Center access denied.")

    @classmethod
    def _sanitize(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "[REDACTED]"
                if cls.SECRET_KEY.search(str(key))
                else cls._sanitize(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [cls._sanitize(item) for item in value]
        return value

    @classmethod
    def _validate_metadata(cls, metadata: dict[str, Any]) -> None:
        if any(cls.SECRET_KEY.search(str(key)) for key in metadata):
            raise ValueError("Secrets are not permitted in Command Center metadata.")

    def _event(
        self,
        scope: CommandCenterScope,
        action: str,
        source: str,
        event_type: ActivityType = ActivityType.AUDIT,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.activity.append(
            ActivityEvent(
                f"activity-{len(self.activity) + 1}",
                scope.tenant,
                scope.workspace,
                event_type,
                scope.actor,
                action,
                source,
                utcnow(),
                self._sanitize(metadata or {}),
            )
        )

    def _put(
        self,
        store: dict[str, ScopedT],
        record: ScopedT,
        scope: CommandCenterScope,
        permission: str,
        source: str,
    ) -> ScopedT:
        self._require(scope, permission)
        self._check(record, scope)
        if record.id in store:
            raise ValueError(f"Duplicate {source} ID: {record.id}")
        store[record.id] = record
        self._event(scope, f"create:{source}", record.id)
        return record

    def create_command_center(
        self, center: CommandCenter, scope: CommandCenterScope
    ) -> CommandCenter:
        self._validate_metadata(center.metadata)
        result = self._put(
            self.command_centers,
            center,
            scope,
            "command_center:create",
            "command-center",
        )
        self.metrics.increment("command_center_instances_total")
        return result

    def set_status(
        self,
        center_id: str,
        status: CommandCenterStatus,
        scope: CommandCenterScope,
        approval_id: str | None = None,
    ) -> CommandCenter:
        self._require(scope, "command_center:control")
        center = self.command_centers[center_id]
        self._check(center, scope)
        if status not in self.ALLOWED_TRANSITIONS[center.status]:
            raise ValueError(
                f"Invalid lifecycle transition: {center.status} -> {status}"
            )
        if status in {CommandCenterStatus.ARCHIVED, CommandCenterStatus.DELETED}:
            self._require(scope, "command_center:approve")
            if not approval_id:
                raise PermissionError(
                    "Approval is required for destructive transitions."
                )
        previous = center.status
        center.status = status
        self._event(
            scope,
            "lifecycle",
            center.id,
            metadata={
                "from": previous.value,
                "to": status.value,
                "approval_id": approval_id,
            },
        )
        return center

    def add_control_plane(
        self, plane: ControlPlane, scope: CommandCenterScope
    ) -> ControlPlane:
        return self._put(
            self.control_planes,
            plane,
            scope,
            "command_center:control",
            "control-plane",
        )

    def synchronize_control_plane(
        self,
        plane_id: str,
        scope: CommandCenterScope,
        health: str,
        synchronization: str = "synchronized",
    ) -> ControlPlane:
        self._require(scope, "command_center:control")
        plane = self.control_planes[plane_id]
        self._check(plane, scope)
        plane.health, plane.synchronization = health, synchronization
        self._event(scope, "synchronize", plane.id, ActivityType.SYSTEM)
        return plane

    def add_operation(
        self, operation: Operation, scope: CommandCenterScope
    ) -> Operation:
        result = self._put(
            self.operations,
            operation,
            scope,
            "command_center:operate",
            "operation",
        )
        self._refresh_gauges(scope)
        return result

    def set_operation_status(
        self,
        operation_id: str,
        status: ExecutionStatus,
        scope: CommandCenterScope,
    ) -> Operation:
        started = time.monotonic()
        self._require(scope, "command_center:operate")
        operation = self.operations[operation_id]
        self._check(operation, scope)
        operation.status = status
        if status in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        }:
            operation.completed_at = utcnow()
        self._event(scope, "operation-status", operation.id, ActivityType.SYSTEM)
        self.metrics.increment(
            "command_center_latency_seconds", time.monotonic() - started
        )
        self._refresh_gauges(scope)
        return operation

    def add_alert(self, alert: Alert, scope: CommandCenterScope) -> Alert:
        result = self._put(self.alerts, alert, scope, "command_center:alert", "alert")
        alert.history.append({"status": alert.status.value, "at": utcnow().isoformat()})
        self._refresh_gauges(scope)
        return result

    def update_alert(
        self,
        alert_id: str,
        status: AlertStatus,
        scope: CommandCenterScope,
        note: str,
    ) -> Alert:
        self._require(scope, "command_center:alert")
        alert = self.alerts[alert_id]
        self._check(alert, scope)
        if status is AlertStatus.ACKNOWLEDGED:
            alert.acknowledgement = note
        elif status is AlertStatus.ESCALATED:
            alert.escalation = note
        elif status is AlertStatus.RESOLVED:
            alert.resolution = note
        alert.status = status
        alert.history.append(
            {
                "status": status.value,
                "actor": scope.actor,
                "note": note,
                "at": utcnow().isoformat(),
            }
        )
        self._event(scope, f"alert:{status.value}", alert.id)
        self._refresh_gauges(scope)
        return alert

    def add_incident(self, incident: Incident, scope: CommandCenterScope) -> Incident:
        result = self._put(
            self.incidents,
            incident,
            scope,
            "command_center:incident",
            "incident",
        )
        incident.timeline.append({"event": "created", "at": utcnow().isoformat()})
        self._refresh_gauges(scope)
        return result

    def resolve_incident(
        self,
        incident_id: str,
        scope: CommandCenterScope,
        resolution: str,
        recovery: str,
        root_cause_reference: str,
        postmortem: str | None = None,
    ) -> Incident:
        self._require(scope, "command_center:incident")
        incident = self.incidents[incident_id]
        self._check(incident, scope)
        incident.status = "resolved"
        incident.resolution = resolution
        incident.recovery = recovery
        incident.root_cause_reference = root_cause_reference
        incident.postmortem = postmortem
        incident.timeline.append(
            {"event": "resolved", "actor": scope.actor, "at": utcnow().isoformat()}
        )
        self._event(scope, "incident:resolved", incident.id)
        self._refresh_gauges(scope)
        return incident

    def add_task(self, task: Task, scope: CommandCenterScope) -> Task:
        if task.retry_limit < 0:
            raise ValueError("Retry limit cannot be negative.")
        for dependency in task.dependencies:
            existing = self.tasks.get(dependency)
            if existing is None:
                raise ValueError(f"Unknown task dependency: {dependency}")
            self._check(existing, scope)
        result = self._put(self.tasks, task, scope, "command_center:task", "task")
        if task.type in {TaskType.AUTOMATED, TaskType.SCHEDULED, TaskType.TRIGGERED}:
            self.metrics.increment("automation_tasks_total")
        return result

    def execute_task(
        self, task_id: str, scope: CommandCenterScope, retry: bool = False
    ) -> Task:
        self._require(scope, "command_center:execute")
        task = self.tasks[task_id]
        self._check(task, scope)
        incomplete = [
            dependency
            for dependency in task.dependencies
            if self.tasks[dependency].execution_status is not ExecutionStatus.COMPLETED
        ]
        if incomplete:
            raise RuntimeError(f"Incomplete task dependencies: {', '.join(incomplete)}")
        if retry:
            if task.retry_count >= task.retry_limit:
                raise RuntimeError("Task retry limit exceeded.")
            task.retry_count += 1
        task.execution_status = ExecutionStatus.RUNNING
        self._event(scope, "task:execute", task.id, ActivityType.AUTOMATION)
        return task

    def add_playbook(self, playbook: Playbook, scope: CommandCenterScope) -> Playbook:
        if not playbook.standard_operating_procedure:
            raise ValueError("A standard operating procedure is required.")
        return self._put(
            self.playbooks,
            playbook,
            scope,
            "command_center:playbook",
            "playbook",
        )

    def execute_playbook(
        self,
        playbook_id: str,
        scope: CommandCenterScope,
        approval_ids: tuple[str, ...] = (),
    ) -> Playbook:
        self._require(scope, "command_center:execute")
        playbook = self.playbooks[playbook_id]
        self._check(playbook, scope)
        missing = set(playbook.approvals) - set(approval_ids)
        if missing:
            raise PermissionError(
                f"Missing playbook approvals: {', '.join(sorted(missing))}"
            )
        playbook.execution_history.append(
            {
                "actor": scope.actor,
                "approvals": list(approval_ids),
                "version": playbook.version,
                "at": utcnow().isoformat(),
            }
        )
        self._event(scope, "playbook:execute", playbook.id, ActivityType.AUTOMATION)
        return playbook

    def add_topology_node(
        self, node: TopologyNode, scope: CommandCenterScope
    ) -> TopologyNode:
        if node.kind not in self.TOPOLOGY_KINDS:
            raise ValueError(f"Unsupported topology node kind: {node.kind}")
        for dependency in node.dependencies:
            existing = self.topology_nodes.get(dependency)
            if existing is None:
                raise ValueError(f"Unknown topology dependency: {dependency}")
            self._check(existing, scope)
        result = self._put(
            self.topology_nodes,
            node,
            scope,
            "command_center:topology",
            "topology-node",
        )
        self.metrics.increment("topology_nodes_total")
        return result

    def record_health(
        self, snapshot: HealthSnapshot, scope: CommandCenterScope
    ) -> HealthSnapshot:
        for value in (
            snapshot.availability,
            snapshot.error_rate,
            snapshot.capacity,
            snapshot.resource_utilization,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Health ratios must be between zero and one.")
        result = self._put(
            self.health_snapshots,
            snapshot,
            scope,
            "command_center:health",
            "health",
        )
        self.metrics.increment("health_checks_total")
        return result

    def activity_feed(
        self,
        scope: CommandCenterScope,
        *,
        query: str = "",
        event_type: ActivityType | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self._require(scope, "command_center:read")
        if not 1 <= limit <= 1000:
            raise ValueError("Activity limit must be between 1 and 1000.")
        lowered = query.casefold()
        events = [
            event
            for event in self.activity
            if event.tenant == scope.tenant
            and event.workspace == scope.workspace
            and (event_type is None or event.type is event_type)
            and (
                not lowered
                or lowered in event.action.casefold()
                or lowered in event.source.casefold()
            )
        ]
        return [self._serialize(event) for event in events[-limit:]]

    def _scoped_values(
        self, store: dict[str, ScopedT], scope: CommandCenterScope
    ) -> list[ScopedT]:
        return [
            record
            for record in store.values()
            if record.tenant == scope.tenant and record.workspace == scope.workspace
        ]

    def _refresh_gauges(self, scope: CommandCenterScope) -> None:
        operations = self._scoped_values(self.operations, scope)
        alerts = self._scoped_values(self.alerts, scope)
        incidents = self._scoped_values(self.incidents, scope)
        self.metrics.set(
            "active_operations_total",
            sum(
                item.status in {ExecutionStatus.QUEUED, ExecutionStatus.RUNNING}
                for item in operations
            ),
        )
        self.metrics.set(
            "active_alerts_total",
            sum(item.status is not AlertStatus.RESOLVED for item in alerts),
        )
        self.metrics.set(
            "active_incidents_total",
            sum(item.status != "resolved" for item in incidents),
        )

    @classmethod
    def _serialize(cls, record: Any) -> dict[str, Any]:
        value = asdict(record)
        for key, item in tuple(value.items()):
            if isinstance(item, Enum):
                value[key] = item.value
            elif isinstance(item, datetime):
                value[key] = item.isoformat()
        return cls._sanitize(value)

    def operations_summary(self, scope: CommandCenterScope) -> dict[str, Any]:
        operations = self._scoped_values(self.operations, scope)
        counts = {status.value: 0 for status in ExecutionStatus}
        for operation in operations:
            counts[operation.status.value] += 1
        return {
            "jobs": counts,
            "automation_status": {
                item.automation_status: sum(
                    candidate.automation_status == item.automation_status
                    for candidate in operations
                )
                for item in operations
            },
            "incident_status": {
                item.incident_status: sum(
                    candidate.incident_status == item.incident_status
                    for candidate in operations
                )
                for item in operations
            },
            "resource_usage": [item.resource_usage for item in operations],
            "capacity": [item.capacity for item in operations],
        }

    def topology(self, scope: CommandCenterScope) -> dict[str, Any]:
        nodes = self._scoped_values(self.topology_nodes, scope)
        return {
            "nodes": [self._serialize(node) for node in nodes],
            "edges": [
                {"source": dependency, "target": node.id}
                for node in nodes
                for dependency in node.dependencies
            ],
            "health_map": {node.id: node.health for node in nodes},
        }

    def dashboard(self, scope: CommandCenterScope) -> dict[str, Any]:
        self._require(scope, "command_center:read")
        return {
            "overview": {
                "instances": len(self._scoped_values(self.command_centers, scope)),
                "control_planes": len(self._scoped_values(self.control_planes, scope)),
            },
            "operations": self.operations_summary(scope),
            "agents": [
                self._serialize(node)
                for node in self._scoped_values(self.topology_nodes, scope)
                if node.kind == "agent"
            ],
            "automation": [
                self._serialize(task)
                for task in self._scoped_values(self.tasks, scope)
                if task.type is not TaskType.MANUAL
            ],
            "incidents": [
                self._serialize(item)
                for item in self._scoped_values(self.incidents, scope)
            ],
            "alerts": [
                self._serialize(item)
                for item in self._scoped_values(self.alerts, scope)
            ],
            "topology": self.topology(scope),
            "health": [
                self._serialize(item)
                for item in self._scoped_values(self.health_snapshots, scope)
            ],
            "activity": self.activity_feed(scope),
            "audit": self.activity_feed(scope, event_type=ActivityType.AUDIT),
            "metrics": self.metrics.snapshot(),
        }

    def resource(self, resource: str, scope: CommandCenterScope) -> Any:
        self._require(scope, "command_center:read")
        mapping: dict[str, dict[str, Any]] = {
            "control-planes": self.control_planes,
            "alerts": self.alerts,
            "incidents": self.incidents,
            "tasks": self.tasks,
            "playbooks": self.playbooks,
            "health": self.health_snapshots,
        }
        if resource == "overview":
            return self.dashboard(scope)["overview"]
        if resource == "operations":
            return self.operations_summary(scope)
        if resource == "topology":
            return self.topology(scope)
        if resource == "activity":
            return self.activity_feed(scope)
        if resource == "dashboard":
            return self.dashboard(scope)
        if resource not in mapping:
            raise KeyError(f"Unknown Command Center resource: {resource}")
        return [
            self._serialize(record)
            for record in self._scoped_values(mapping[resource], scope)
        ]
