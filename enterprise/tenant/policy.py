"""Tenant policy contract and deterministic non-enforcing reference validator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .context import TenantContext
from .isolation import TenantIsolationDescriptor
from .routing import TenantRoutingRequest
from .tenant import OrganizationTenantBinding, Tenant


@dataclass(frozen=True, slots=True)
class TenantPolicyResult:
    """Validation result that does not make an access or routing decision."""

    valid: bool
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class TenantPolicy(Protocol):
    """Optional explicit validation boundary for tenant descriptors and requests."""

    def validate_creation(self, tenant: Tenant) -> TenantPolicyResult: ...
    def validate_transition(
        self, tenant: Tenant, action: str
    ) -> TenantPolicyResult: ...
    def validate_context(self, context: TenantContext) -> TenantPolicyResult: ...
    def validate_binding(
        self, binding: OrganizationTenantBinding
    ) -> TenantPolicyResult: ...
    def validate_isolation(
        self, descriptor: TenantIsolationDescriptor
    ) -> TenantPolicyResult: ...
    def validate_routing(self, request: TenantRoutingRequest) -> TenantPolicyResult: ...


class ReferenceTenantPolicy:
    """Reference-only validator that never grants, blocks, or routes access."""

    def validate_creation(self, tenant: Tenant) -> TenantPolicyResult:
        """Accept an already-valid immutable tenant descriptor."""
        return TenantPolicyResult(True)

    def validate_transition(self, tenant: Tenant, action: str) -> TenantPolicyResult:
        """Require a non-empty declarative action only."""
        return TenantPolicyResult(
            bool(action), (() if action else ("action required",))
        )

    def validate_context(self, context: TenantContext) -> TenantPolicyResult:
        """Require caller-provided tenant context without resolving it."""
        return TenantPolicyResult(
            bool(context.tenant_id),
            (() if context.tenant_id else ("tenant id required",)),
        )

    def validate_binding(
        self, binding: OrganizationTenantBinding
    ) -> TenantPolicyResult:
        """Accept a constructed binding without organization synchronization."""
        return TenantPolicyResult(True)

    def validate_isolation(
        self, descriptor: TenantIsolationDescriptor
    ) -> TenantPolicyResult:
        """Describe a valid descriptor without claiming actual isolation."""
        return TenantPolicyResult(True, warnings=("descriptor only",))

    def validate_routing(self, request: TenantRoutingRequest) -> TenantPolicyResult:
        """Validate explicit context without selecting a route."""
        return self.validate_context(request.context)
