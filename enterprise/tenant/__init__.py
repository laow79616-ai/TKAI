"""Offline Enterprise Tenant Boundary Foundation contracts and reference fakes."""

from .context import (
    TenantContext,
    optional_tenant,
    require_tenant,
    system_tenant_context,
)
from .descriptor import TenantDescriptor
from .factory import TenantFactory
from .isolation import (
    TenantIsolationDecision,
    TenantIsolationDescriptor,
    TenantIsolationMode,
)
from .lifecycle import (
    ReferenceTenantLifecycle,
    TenantLifecycleEvent,
    TenantLifecycleState,
)
from .policy import ReferenceTenantPolicy, TenantPolicy, TenantPolicyResult
from .quota import (
    ReferenceTenantQuotaService,
    TenantQuota,
    TenantQuotaDecision,
    TenantQuotaLimit,
    TenantQuotaResource,
    TenantQuotaUsage,
)
from .registry import TenantRegistry
from .resolver import ReferenceTenantResolver, TenantResolver
from .routing import (
    ReferenceTenantRoutingPolicy,
    TenantRoute,
    TenantRoutingDecision,
    TenantRoutingPolicy,
    TenantRoutingRequest,
)
from .tenant import (
    OrganizationTenantBinding,
    Tenant,
    TenantAccessDescriptor,
    TenantMembershipDescriptor,
    TenantStatus,
)

__all__ = (
    "OrganizationTenantBinding",
    "ReferenceTenantLifecycle",
    "ReferenceTenantPolicy",
    "ReferenceTenantQuotaService",
    "ReferenceTenantResolver",
    "ReferenceTenantRoutingPolicy",
    "Tenant",
    "TenantAccessDescriptor",
    "TenantContext",
    "TenantDescriptor",
    "TenantFactory",
    "TenantIsolationDecision",
    "TenantIsolationDescriptor",
    "TenantIsolationMode",
    "TenantLifecycleEvent",
    "TenantLifecycleState",
    "TenantMembershipDescriptor",
    "TenantPolicy",
    "TenantPolicyResult",
    "TenantQuota",
    "TenantQuotaDecision",
    "TenantQuotaLimit",
    "TenantQuotaResource",
    "TenantQuotaUsage",
    "TenantRegistry",
    "TenantResolver",
    "TenantRoute",
    "TenantRoutingDecision",
    "TenantRoutingPolicy",
    "TenantRoutingRequest",
    "TenantStatus",
    "optional_tenant",
    "require_tenant",
    "system_tenant_context",
)
