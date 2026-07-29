"""Immutable contracts for the V7 workflow orchestration framework."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, cast

from tkai.v7.security import filter_secrets


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowLifecycle(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    READY = "ready"
    PLANNED = "planned"
    QUEUED = "queued"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True)
class WorkflowScope:
    tenant_reference: str
    workspace_reference: str


@dataclass(frozen=True)
class Dependency:
    workflow_id: str
    required_version: str | None = None
    optional: bool = False


@dataclass(frozen=True)
class Constraint:
    name: str
    satisfied: bool = True
    reference: str | None = None
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", filter_secrets(self.details))


@dataclass(frozen=True)
class ScheduleMetadata:
    window_start: str | None = None
    window_end: str | None = None
    priority: int = 0
    queue: str = "default"


@dataclass(frozen=True)
class Workflow:
    workflow_id: str
    name: str
    version: str
    owner: str
    category: str
    definition: Mapping[str, object]
    state_reference: str
    scope: WorkflowScope
    dependencies: tuple[Dependency, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    lifecycle: WorkflowLifecycle = WorkflowLifecycle.DRAFT
    schedule: ScheduleMetadata = field(default_factory=ScheduleMetadata)
    metrics: Mapping[str, float] = field(default_factory=dict)
    audit: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        required = (
            self.workflow_id,
            self.name,
            self.version,
            self.owner,
            self.category,
            self.state_reference,
        )
        if not all(required):
            raise ValueError("workflow identity and state reference are required")
        object.__setattr__(self, "definition", filter_secrets(self.definition))
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    workflow_id: str
    severity: str = "error"


@dataclass(frozen=True)
class ValidationReport:
    workflow_id: str
    valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    checked_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class WorkflowPlan:
    plan_id: str
    workflow_id: str
    ordered_workflow_ids: tuple[str, ...]
    ready: bool
    bounded: bool
    reference_only: bool = True
    issues: tuple[str, ...] = ()
    schedule: ScheduleMetadata = field(default_factory=ScheduleMetadata)
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class RecoveryPlan:
    recovery_id: str
    workflow_id: str
    strategy: str
    target_reference: str
    ready: bool
    rollback: bool = False
    coordinated: bool = True
    reference_only: bool = True
    issues: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class HistoryEntry:
    entry_id: str
    workflow_id: str
    category: str
    action: str
    actor: str
    reference: str | None = None
    details: Mapping[str, object] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", filter_secrets(self.details))


def serialize(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: serialize(item) for key, item in asdict(cast(Any, value)).items()}
    if isinstance(value, Mapping):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [serialize(item) for item in value]
    return value


WorkflowDefinition = Workflow

__all__ = (
    "Constraint",
    "Dependency",
    "HistoryEntry",
    "RecoveryPlan",
    "ScheduleMetadata",
    "ValidationIssue",
    "ValidationReport",
    "Workflow",
    "WorkflowDefinition",
    "WorkflowLifecycle",
    "WorkflowPlan",
    "WorkflowScope",
    "serialize",
    "utc_now",
)
