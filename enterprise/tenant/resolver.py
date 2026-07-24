"""Explicit tenant resolver contract and deterministic mapping-based reference fake."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from .context import TenantContext, require_tenant
from .errors import TenantNotFoundError, TenantResolutionError
from .tenant import Tenant


class TenantResolver(Protocol):
    """Resolves caller-supplied tenant data without headers, JWTs, or databases."""

    def resolve(self, context: TenantContext) -> Tenant: ...
    def validate(self, context: TenantContext) -> bool: ...
    def capabilities(self) -> frozenset[str]: ...


class ReferenceTenantResolver:
    """Reference-only resolver backed by an injected tenant mapping."""

    def __init__(self, tenants: Mapping[str, Tenant]) -> None:
        self._tenants = dict(tenants)

    def resolve(self, context: TenantContext) -> Tenant:
        """Resolve an explicit id and preserve lookup errors through chaining."""
        tenant_id = require_tenant(context).tenant_id
        assert tenant_id is not None
        try:
            tenant = self._tenants[tenant_id]
        except KeyError as exc:
            raise TenantResolutionError(
                f"Tenant {tenant_id!r} could not be resolved."
            ) from exc
        if (
            context.organization_id
            and context.organization_id != tenant.organization_id
        ):
            cause = TenantNotFoundError(tenant_id)
            raise TenantResolutionError(
                "Tenant does not match supplied organization."
            ) from cause
        return tenant

    def validate(self, context: TenantContext) -> bool:
        """Return whether resolution succeeds without creating a tenant."""
        try:
            self.resolve(context)
        except TenantResolutionError:
            return False
        return True

    def capabilities(self) -> frozenset[str]:
        """Describe explicit mapping lookup only."""
        return frozenset({"explicit_tenant_id", "organization_validation"})
