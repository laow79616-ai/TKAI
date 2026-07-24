"""Explicit tenant context helpers with no global, environment, or ContextVar state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .errors import TenantValidationError
from .tenant import TenantValue, snapshot


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Caller-provided tenant scope that never infers identity or ownership."""

    tenant_id: str | None = None
    organization_id: str | None = None
    workspace_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    region: str | None = None
    metadata: Mapping[str, TenantValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe snapshot with explicit absent tenant semantics."""
        return {
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "region": self.region,
            "metadata": dict(self.metadata),
        }


def require_tenant(context: TenantContext | None) -> TenantContext:
    """Return an explicit tenant context or raise a stable validation error."""
    if context is None or not context.tenant_id:
        raise TenantValidationError("An explicit tenant context is required.")
    return context


def optional_tenant(context: TenantContext | None) -> TenantContext | None:
    """Return caller input unchanged, including absent tenant context."""
    return context


def system_tenant_context(tenant_id: str, organization_id: str) -> TenantContext:
    """Build explicit system scope without resolving a system identity."""
    return TenantContext(tenant_id, organization_id, user_id="system")
