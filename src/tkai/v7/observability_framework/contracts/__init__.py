"""Immutable contracts for the V7 Unified Observability Framework."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, cast

from tkai.v7.security import filter_secrets


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Severity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ObservationLifecycle(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class ObservationScope:
    tenant: str
    workspace: str


@dataclass(frozen=True)
class Observation:
    observation_id: str
    source: str
    category: str
    component: str
    scope: ObservationScope
    severity: Severity = Severity.INFO
    timestamp: str = field(default_factory=utc_now)
    correlation_id: str | None = None
    trace_id: str | None = None
    health_status: HealthStatus = HealthStatus.UNKNOWN
    metric_reference: str | None = None
    audit_reference: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)
    lifecycle: ObservationLifecycle = ObservationLifecycle.ACTIVE

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    description: str
    unit: str
    scope: ObservationScope
    aggregation: str = "last"
    sampling: Mapping[str, object] = field(default_factory=dict)
    retention: Mapping[str, object] = field(default_factory=dict)
    compatibility: frozenset[str] = frozenset({"6", "7"})
    metadata: Mapping[str, object] = field(default_factory=dict)
    reference_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "sampling", filter_secrets(self.sampling))
        object.__setattr__(self, "retention", filter_secrets(self.retention))
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class MetricSample:
    metric_reference: str
    value: float
    scope: ObservationScope
    timestamp: str = field(default_factory=utc_now)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class LogRecord:
    message: str
    classification: str
    component: str
    scope: ObservationScope
    severity: Severity = Severity.INFO
    correlation_id: str | None = None
    trace_id: str | None = None
    retention: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))
        object.__setattr__(self, "retention", filter_secrets(self.retention))


@dataclass(frozen=True)
class Span:
    trace_id: str
    span_id: str
    name: str
    component: str
    scope: ObservationScope
    parent_span_id: str | None = None
    correlation_id: str | None = None
    lifecycle: ObservationLifecycle = ObservationLifecycle.ACTIVE
    metadata: Mapping[str, object] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class DiagnosticResult:
    diagnostic_id: str
    category: str
    component: str
    scope: ObservationScope
    status: HealthStatus
    summary: str
    recommendations: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)
    read_only: bool = True
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class HealthRecord:
    component: str
    kind: str
    scope: ObservationScope
    status: HealthStatus
    details: Mapping[str, object] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", filter_secrets(self.details))


@dataclass(frozen=True)
class Alert:
    alert_id: str
    component: str
    scope: ObservationScope
    severity: Severity
    threshold: Mapping[str, object]
    suppression: Mapping[str, object] = field(default_factory=dict)
    acknowledgement: Mapping[str, object] = field(default_factory=dict)
    recommendations: tuple[str, ...] = ()
    lifecycle: ObservationLifecycle = ObservationLifecycle.ACTIVE
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "threshold", filter_secrets(self.threshold))
        object.__setattr__(self, "suppression", filter_secrets(self.suppression))
        object.__setattr__(
            self, "acknowledgement", filter_secrets(self.acknowledgement)
        )


@dataclass(frozen=True)
class AuditCorrelation:
    correlation_id: str
    scope: ObservationScope
    audit_references: tuple[str, ...] = ()
    trace_references: tuple[str, ...] = ()
    metric_references: tuple[str, ...] = ()
    health_references: tuple[str, ...] = ()
    event_references: tuple[str, ...] = ()
    timestamp: str = field(default_factory=utc_now)


def serialize(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: serialize(item) for key, item in asdict(cast(Any, value)).items()}
    if isinstance(value, Mapping):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    return value


__all__ = (
    "Alert",
    "AuditCorrelation",
    "DiagnosticResult",
    "HealthRecord",
    "HealthStatus",
    "LogRecord",
    "MetricDefinition",
    "MetricSample",
    "Observation",
    "ObservationLifecycle",
    "ObservationScope",
    "Severity",
    "Span",
    "serialize",
)
