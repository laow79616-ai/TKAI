"""Immutable contracts for the V7 Unified Security and Policy Framework."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, cast

from tkai.v7.security import filter_secrets


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PolicyType(str, Enum):
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    COMPLIANCE = "compliance"
    INTEGRITY = "integrity"
    ISOLATION = "isolation"


class PolicyLifecycle(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class Effect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ADVISE = "advise"


@dataclass(frozen=True)
class SecurityScope:
    tenant: str
    workspace: str
    capability: str | None = None
    service: str | None = None


@dataclass(frozen=True)
class Permission:
    permission_id: str
    capability: str
    description: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class Role:
    role_id: str
    permissions: frozenset[str] = frozenset()
    parents: frozenset[str] = frozenset()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class Principal:
    principal_id: str
    roles: frozenset[str] = frozenset()
    tenant: str | None = None
    workspace: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class PolicyRule:
    permission: str
    effect: Effect = Effect.ALLOW
    roles: frozenset[str] = frozenset()
    principals: frozenset[str] = frozenset()
    conditions: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "conditions", filter_secrets(self.conditions))


@dataclass(frozen=True)
class Policy:
    policy_id: str
    policy_type: PolicyType
    rules: tuple[PolicyRule, ...]
    scope: SecurityScope
    lifecycle: PolicyLifecycle = PolicyLifecycle.ACTIVE
    priority: int = 0
    metadata: Mapping[str, object] = field(default_factory=dict)
    audit: tuple[str, ...] = ()
    health: str = "healthy"
    metrics: Mapping[str, float] = field(default_factory=dict)
    compatible_versions: frozenset[str] = frozenset({"6", "7"})
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class AuthorizationRequest:
    principal: Principal
    permission: str
    scope: SecurityScope
    capability: str | None = None
    service: str | None = None
    context: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "context", filter_secrets(self.context))


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str
    principal_id: str
    permission: str
    matched_policy_ids: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    reference_only: bool = True
    evaluated_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"
    reference: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    recommendations: tuple[str, ...] = ()
    checked_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class SecretReference:
    secret_id: str
    provider: str
    reference: str
    classification: str = "secret"
    rotation_due_at: str | None = None
    version: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.reference or "://" not in self.reference:
            raise ValueError("secret must use an opaque reference")
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    category: str
    action: str
    actor: str
    outcome: str
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
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    return value


__all__ = (
    "AuditEvent",
    "AuthorizationDecision",
    "AuthorizationRequest",
    "Effect",
    "Permission",
    "Policy",
    "PolicyLifecycle",
    "PolicyRule",
    "PolicyType",
    "Principal",
    "Role",
    "SecretReference",
    "SecurityScope",
    "ValidationIssue",
    "ValidationReport",
    "serialize",
    "utc_now",
)
