"""Immutable contracts for the local-only V7 Unified Event Fabric."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Protocol, runtime_checkable

from tkai.v7.contracts import Version, VersionRange
from tkai.v7.security import filter_secrets


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventLifecycle(str, Enum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ROUTED = "routed"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    RETRYING = "retrying"
    DEAD_LETTERED = "dead_lettered"
    REPLAYED = "replayed"
    EXPIRED = "expired"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class DeliveryMode(str, Enum):
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once_simulation"
    BEST_EFFORT = "best_effort"


class OrderingMode(str, Enum):
    NONE = "none"
    SOURCE = "source"
    SUBJECT = "subject"
    CORRELATION = "correlation"
    PARTITION_KEY = "partition_key"


class IntegrityStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    UNVERIFIED = "unverified"


class FailureClass(str, Enum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    UNAUTHORIZED = "unauthorized"
    INVALID = "invalid"


@dataclass(frozen=True)
class DeliveryPolicy:
    mode: DeliveryMode = DeliveryMode.AT_MOST_ONCE
    acknowledgement_required: bool = False
    timeout_seconds: float = 5.0


@dataclass(frozen=True)
class RetryPolicy:
    policy_id: str = "default"
    maximum_attempts: int = 3
    backoff_seconds: tuple[float, ...] = (0.0, 1.0, 2.0)
    retryable: frozenset[FailureClass] = frozenset(
        {FailureClass.TRANSIENT, FailureClass.TIMEOUT}
    )

    def delay(self, attempt: int) -> float:
        if not self.backoff_seconds:
            return 0.0
        index = min(max(attempt - 1, 0), len(self.backoff_seconds) - 1)
        return self.backoff_seconds[index]


@dataclass(frozen=True)
class DeadLetterPolicy:
    policy_id: str = "default"
    enabled: bool = True


@dataclass(frozen=True)
class ReplayPolicy:
    policy_id: str = "default"
    maximum_events: int = 100
    maximum_replays: int = 3
    approval_required: bool = True


@dataclass(frozen=True)
class RetentionPolicy:
    policy_id: str = "default"
    maximum_age_seconds: int = 86400


@dataclass(frozen=True)
class SecurityPolicy:
    policy_id: str = "default"
    require_integrity: bool = True
    require_tenant_workspace: bool = True


@dataclass(frozen=True)
class AuditPolicy:
    policy_id: str = "default"
    enabled: bool = True


@dataclass(frozen=True)
class IsolationPolicy:
    policy_id: str = "default"
    enforce_tenant: bool = True
    enforce_workspace: bool = True


@dataclass(frozen=True)
class EventModel:
    event_id: str
    event_type: str
    event_version: Version
    source: str
    subject: str
    tenant_reference: str
    workspace_reference: str
    payload_reference: str
    correlation_id: str | None = None
    causation_id: str | None = None
    trace_id: str | None = None
    timestamp: str = field(default_factory=utc_now)
    headers: Mapping[str, object] = field(default_factory=dict)
    priority: int = 100
    delivery_policy: str = "default"
    retention_policy: str = "default"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class EventEnvelope:
    event: EventModel
    schema_version: str = "1.0"
    payload_hash: str = ""
    integrity_status: IntegrityStatus = IntegrityStatus.UNVERIFIED
    metadata: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event: EventModel,
        *,
        payload_metadata: Mapping[str, object] | None = None,
        maximum_metadata_items: int = 32,
    ) -> EventEnvelope:
        safe = bounded_metadata(payload_metadata or {}, maximum_metadata_items)
        digest = sha256(event.payload_reference.encode("utf-8")).hexdigest()
        return cls(
            event=sanitize_event(event),
            payload_hash=digest,
            integrity_status=IntegrityStatus.VALID,
            metadata=safe,
        )

    def verify(self) -> bool:
        expected = sha256(self.event.payload_reference.encode("utf-8")).hexdigest()
        return self.payload_hash == expected

    def serialize(self) -> str:
        return json.dumps(serialize(self), sort_keys=True, separators=(",", ":"))

    @classmethod
    def deserialize(cls, value: str) -> EventEnvelope:
        raw = json.loads(value)
        event_raw = raw["event"]
        event_raw["event_version"] = Version.parse(event_raw["event_version"])
        event = EventModel(**event_raw)
        return cls(
            event=event,
            schema_version=raw["schema_version"],
            payload_hash=raw["payload_hash"],
            integrity_status=IntegrityStatus(raw["integrity_status"]),
            metadata=raw.get("metadata", {}),
        )


@dataclass(frozen=True)
class EventContract:
    event_type: str
    version: Version
    schema: Mapping[str, object] = field(default_factory=dict)
    publisher_references: tuple[str, ...] = ()
    compatibility: VersionRange = field(
        default_factory=lambda: VersionRange(Version(0), Version(999, 999, 999))
    )
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Publisher:
    publisher_id: str
    event_types: frozenset[str]
    capability_references: frozenset[str] = frozenset()
    service_reference: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@runtime_checkable
class SubscriberHandler(Protocol):
    def __call__(self, envelope: EventEnvelope) -> object: ...


@dataclass(frozen=True)
class Subscriber:
    subscriber_id: str
    capability_references: frozenset[str] = frozenset()
    service_reference: str | None = None
    health_state: str = "healthy"
    lifecycle_state: str = "active"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class EventFilter:
    event_types: frozenset[str] = frozenset()
    versions: VersionRange | None = None
    sources: frozenset[str] = frozenset()
    subjects: frozenset[str] = frozenset()
    tenants: frozenset[str] = frozenset()
    workspaces: frozenset[str] = frozenset()
    priorities: frozenset[int] = frozenset()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def matches(self, event: EventModel) -> bool:
        return all(
            (
                not self.event_types or event.event_type in self.event_types,
                self.versions is None or self.versions.supports(event.event_version),
                not self.sources or event.source in self.sources,
                not self.subjects or event.subject in self.subjects,
                not self.tenants or event.tenant_reference in self.tenants,
                not self.workspaces or event.workspace_reference in self.workspaces,
                not self.priorities or event.priority in self.priorities,
                all(
                    event.metadata.get(key) == value
                    for key, value in self.metadata.items()
                ),
            )
        )


@dataclass(frozen=True)
class Subscription:
    subscription_id: str
    event_type: str
    versions: VersionRange
    subscriber_reference: str
    filter_reference: str | None = None
    priority: int = 100
    delivery_mode: DeliveryMode = DeliveryMode.AT_MOST_ONCE
    retry_policy: str = "default"
    dead_letter_policy: str = "default"
    replay_policy: str = "default"
    status: str = "active"
    tenant_reference: str | None = None
    workspace_reference: str | None = None
    fallback: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DeliveryResult:
    event_id: str
    subscriber_reference: str
    delivered: bool
    acknowledged: bool = False
    attempts: int = 1
    latency_seconds: float = 0.0
    failure_class: FailureClass | None = None
    reason: str | None = None


@dataclass(frozen=True)
class RetryRecord:
    event_id: str
    subscriber_reference: str
    attempt: int
    failure_class: FailureClass
    delay_seconds: float
    timestamp: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class DeadLetterRecord:
    record_id: str
    event_reference: str
    failure_reason: str
    delivery_attempts: int
    subscriber_reference: str
    policy_reference: str
    timestamp: str = field(default_factory=utc_now)
    review_status: str = "pending"
    replay_eligible: bool = True
    audit_reference: str | None = None


@dataclass(frozen=True)
class ReplayRequest:
    request_id: str
    event_reference: str | None = None
    time_range: tuple[str, str] | None = None
    subscriber_scope: tuple[str, ...] = ()
    reason: str = ""
    approval_reference: str | None = None
    status: str = "requested"
    maximum_results: int = 100
    maximum_replays: int = 1
    audit_reference: str | None = None


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    fingerprint: str
    subscriber_scope: str
    time_window_seconds: int = 3600
    timestamp: str = field(default_factory=utc_now)
    duplicate: bool = False
    outcome: str = "accepted"


def bounded_metadata(
    values: Mapping[str, object], maximum: int = 32
) -> dict[str, object]:
    if len(values) > maximum:
        raise ValueError("payload metadata exceeds bounded item limit")
    if len(json.dumps(values, default=str).encode("utf-8")) > 8192:
        raise ValueError("payload metadata exceeds bounded size limit")
    sensitive = (
        "authorization",
        "cookie",
        "session",
        "proxy",
        "credential",
    )

    def clean(current: Mapping[str, object]) -> dict[str, object]:
        filtered = filter_secrets(current)
        return {
            key: (
                "[REDACTED]"
                if any(marker in key.lower() for marker in sensitive)
                else clean(value)
                if isinstance(value, Mapping)
                else value
            )
            for key, value in filtered.items()
        }

    return clean(values)


def sanitize_event(event: EventModel) -> EventModel:
    from dataclasses import replace

    if not event.payload_reference or "://" not in event.payload_reference:
        raise ValueError("payload_reference must be an opaque reference URI")
    forbidden = ("cookie", "session", "proxy", "password", "secret", "credential")
    if any(marker in event.payload_reference.lower() for marker in forbidden):
        raise ValueError("payload_reference contains prohibited sensitive material")
    return replace(
        event,
        headers=bounded_metadata(event.headers),
        metadata=bounded_metadata(event.metadata),
    )


def serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Version):
        return str(value)
    if isinstance(value, VersionRange):
        return {"minimum": str(value.minimum), "maximum": str(value.maximum)}
    if hasattr(value, "__dataclass_fields__"):
        return filter_secrets(
            {key: serialize(item) for key, item in vars(value).items()}
        )
    if isinstance(value, Mapping):
        return filter_secrets(
            {str(key): serialize(item) for key, item in value.items()}
        )
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    return value


__all__ = (
    "AuditPolicy",
    "DeadLetterPolicy",
    "DeadLetterRecord",
    "DeliveryMode",
    "DeliveryPolicy",
    "DeliveryResult",
    "EventContract",
    "EventEnvelope",
    "EventFilter",
    "EventLifecycle",
    "EventModel",
    "FailureClass",
    "IdempotencyRecord",
    "IntegrityStatus",
    "IsolationPolicy",
    "OrderingMode",
    "Publisher",
    "ReplayPolicy",
    "ReplayRequest",
    "RetentionPolicy",
    "RetryPolicy",
    "RetryRecord",
    "SecurityPolicy",
    "Subscriber",
    "SubscriberHandler",
    "Subscription",
    "bounded_metadata",
    "serialize",
)
