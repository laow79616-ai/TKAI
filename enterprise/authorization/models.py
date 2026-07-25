"""Immutable authorization and ABAC extension descriptors without enforcement."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

AuthorizationValue = str | int | float | bool | None


def snapshot(
    value: Mapping[str, AuthorizationValue],
) -> Mapping[str, AuthorizationValue]:
    """Return a read-only defensive mapping snapshot."""
    return MappingProxyType(dict(value))


class AuthorizationOutcome(str, Enum):
    """Possible descriptive outcomes from an explicitly invoked service."""

    ALLOWED = "allowed"
    DENIED = "denied"
    NOT_APPLICABLE = "not_applicable"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class ScopeDescriptor:
    """Declares an organization, tenant, workspace, or other scope identifier."""

    kind: str
    scope_id: str


@dataclass(frozen=True, slots=True)
class ResourceDescriptor:
    """Declares a resource type and optional resource identifier."""

    resource_type: str
    resource_id: str | None = None


@dataclass(frozen=True, slots=True)
class ActionDescriptor:
    """Declares a requested action without invoking it."""

    name: str


@dataclass(frozen=True, slots=True)
class PermissionDescriptor:
    """RBAC permission descriptor with explicit resource, action, and scopes."""

    permission_id: str
    resource: ResourceDescriptor
    action: ActionDescriptor
    scopes: tuple[ScopeDescriptor, ...] = ()
    metadata: Mapping[str, AuthorizationValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.permission_id:
            raise ValueError("Permission descriptor id must not be empty.")
        object.__setattr__(self, "scopes", tuple(self.scopes))
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class RoleDescriptor:
    """RBAC role descriptor with declared permission ids only."""

    role_id: str
    name: str
    permission_ids: frozenset[str] = field(default_factory=frozenset)
    scopes: tuple[ScopeDescriptor, ...] = ()

    def __post_init__(self) -> None:
        if not self.role_id or not self.name:
            raise ValueError("Role descriptor id and name must not be empty.")
        object.__setattr__(self, "permission_ids", frozenset(self.permission_ids))
        object.__setattr__(self, "scopes", tuple(self.scopes))


@dataclass(frozen=True, slots=True)
class AuthorizationContext:
    """Explicit authorization input with no ambient identity or tenant lookup."""

    subject_id: str | None = None
    role_ids: frozenset[str] = field(default_factory=frozenset)
    organization_id: str | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    metadata: Mapping[str, AuthorizationValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "role_ids", frozenset(self.role_ids))
        object.__setattr__(self, "metadata", snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe context representation."""
        return {
            "subject_id": self.subject_id,
            "role_ids": sorted(self.role_ids),
            "organization_id": self.organization_id,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    """Explicit request to describe an authorization decision."""

    context: AuthorizationContext
    permission: PermissionDescriptor


@dataclass(frozen=True, slots=True)
class AuthorizationExplanation:
    """Structured, non-secret explanation for a descriptive decision."""

    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    """Immutable outcome; callers decide whether and how to act on it."""

    outcome: AuthorizationOutcome
    explanation: AuthorizationExplanation = field(
        default_factory=AuthorizationExplanation
    )

    @property
    def allowed(self) -> bool:
        """Return whether the descriptive outcome is allowed."""
        return self.outcome is AuthorizationOutcome.ALLOWED

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe decision representation."""
        return {
            "outcome": self.outcome.value,
            "reasons": list(self.explanation.reasons),
            "warnings": list(self.explanation.warnings),
        }


@dataclass(frozen=True, slots=True)
class AuthorizationCapability:
    """Declares a service capability without probing external systems."""

    name: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class Attribute:
    """ABAC extension attribute; no policy expression is evaluated."""

    name: str
    value: AuthorizationValue


@dataclass(frozen=True, slots=True)
class Subject:
    """ABAC extension subject descriptor with safe attributes."""

    subject_id: str
    attributes: tuple[Attribute, ...] = ()


@dataclass(frozen=True, slots=True)
class Resource:
    """ABAC extension resource descriptor with safe attributes."""

    resource: ResourceDescriptor
    attributes: tuple[Attribute, ...] = ()


@dataclass(frozen=True, slots=True)
class Environment:
    """ABAC extension environment descriptor with caller-provided attributes."""

    attributes: tuple[Attribute, ...] = ()
