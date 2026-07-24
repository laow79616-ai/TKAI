"""Immutable audit descriptors, events, and query models without persistence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType

AuditValue = str | int | float | bool | None


def snapshot(value: Mapping[str, AuditValue]) -> Mapping[str, AuditValue]:
    """Return a read-only defensive metadata snapshot."""
    return MappingProxyType(dict(value))


class AuditActorKind(str, Enum):
    ANONYMOUS = "anonymous"
    SYSTEM = "system"
    USER = "user"
    SERVICE = "service"
    BOT = "bot"
    EXTERNAL = "external"


class AuditTargetKind(str, Enum):
    ORGANIZATION = "organization"
    TENANT = "tenant"
    WORKSPACE = "workspace"
    TEAM = "team"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    WORKFLOW = "workflow"
    EXECUTION = "execution"
    AGENT = "agent"
    PROVIDER = "provider"
    MEMORY = "memory"
    TOOL = "tool"
    PLUGIN = "plugin"
    SYSTEM = "system"
    CUSTOM = "custom"


class AuditOutcomeStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    CANCELLED = "cancelled"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class AuditCategory(str, Enum):
    IDENTITY = "identity"
    ORGANIZATION = "organization"
    TENANT = "tenant"
    AUTHORIZATION = "authorization"
    WORKFLOW = "workflow"
    EXECUTION = "execution"
    CONFIGURATION = "configuration"
    LICENSING = "licensing"
    ADMINISTRATION = "administration"
    SECURITY = "security"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class AuditContext:
    tenant_id: str | None = None
    organization_id: str | None = None
    workspace_id: str | None = None
    user_id: str | None = None
    principal_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    source: str = "explicit"
    metadata: Mapping[str, AuditValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe context snapshot."""
        return {
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "principal_id": self.principal_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class AuditActor:
    actor_id: str
    kind: AuditActorKind
    display_name: str
    tenant_id: str | None = None
    organization_id: str | None = None
    attributes: Mapping[str, AuditValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attributes", snapshot(self.attributes))


@dataclass(frozen=True, slots=True)
class AuditTarget:
    target_id: str
    kind: AuditTargetKind
    name: str
    parent_id: str | None = None
    metadata: Mapping[str, AuditValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class AuditOutcome:
    status: AuditOutcomeStatus
    reason: str | None = None
    error_type: str | None = None
    error_code: str | None = None
    metadata: Mapping[str, AuditValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    timestamp: datetime
    action: str
    category: AuditCategory
    actor: AuditActor
    target: AuditTarget
    outcome: AuditOutcome
    context: AuditContext
    sequence: int | None = None
    metadata: Mapping[str, AuditValue] = field(default_factory=dict)
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if not self.event_id or not self.action or not self.schema_version:
            raise ValueError("Audit event id, action, and schema version are required.")
        if self.timestamp.tzinfo is None:
            raise ValueError("Audit event timestamp must be timezone-aware.")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(timezone.utc))
        object.__setattr__(self, "metadata", snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "category": self.category.value,
            "actor": {
                "actor_id": self.actor.actor_id,
                "kind": self.actor.kind.value,
                "display_name": self.actor.display_name,
                "tenant_id": self.actor.tenant_id,
                "organization_id": self.actor.organization_id,
                "attributes": dict(self.actor.attributes),
            },
            "target": {
                "target_id": self.target.target_id,
                "kind": self.target.kind.value,
                "name": self.target.name,
                "parent_id": self.target.parent_id,
                "metadata": dict(self.target.metadata),
            },
            "outcome": {
                "status": self.outcome.status.value,
                "reason": self.outcome.reason,
                "error_type": self.outcome.error_type,
                "error_code": self.outcome.error_code,
                "metadata": dict(self.outcome.metadata),
            },
            "context": self.context.to_dict(),
            "request_id": self.context.request_id,
            "correlation_id": self.context.correlation_id,
            "sequence": self.sequence,
            "metadata": dict(self.metadata),
            "schema_version": self.schema_version,
        }


class AuditSort(str, Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


@dataclass(frozen=True, slots=True)
class AuditPage:
    offset: int = 0
    limit: int = 100

    def __post_init__(self) -> None:
        if self.offset < 0 or self.limit < 1:
            raise ValueError(
                "Audit page offset must be non-negative and limit positive."
            )


@dataclass(frozen=True, slots=True)
class AuditQuery:
    event_id: str | None = None
    actor_id: str | None = None
    target_id: str | None = None
    action: str | None = None
    category: AuditCategory | None = None
    outcome_status: AuditOutcomeStatus | None = None
    tenant_id: str | None = None
    organization_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    metadata_key: str | None = None
    metadata_value: AuditValue = None
    page: AuditPage = field(default_factory=AuditPage)
    sort: AuditSort = AuditSort.ASCENDING


@dataclass(frozen=True, slots=True)
class AuditQueryResult:
    events: tuple[AuditEvent, ...]
    total: int
    next_cursor: str | None = None
