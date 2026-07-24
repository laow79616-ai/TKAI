"""Offline tests for the explicit Enterprise Tenant Boundary Foundation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from enterprise.tenant import (
    OrganizationTenantBinding,
    ReferenceTenantLifecycle,
    ReferenceTenantPolicy,
    ReferenceTenantQuotaService,
    ReferenceTenantResolver,
    ReferenceTenantRoutingPolicy,
    Tenant,
    TenantAccessDescriptor,
    TenantContext,
    TenantDescriptor,
    TenantFactory,
    TenantIsolationDecision,
    TenantIsolationDescriptor,
    TenantIsolationMode,
    TenantLifecycleState,
    TenantMembershipDescriptor,
    TenantQuota,
    TenantQuotaLimit,
    TenantQuotaResource,
    TenantQuotaUsage,
    TenantRegistry,
    TenantRoute,
    TenantRoutingRequest,
    TenantStatus,
    optional_tenant,
    require_tenant,
    system_tenant_context,
)
from enterprise.tenant.errors import (
    TenantConflictError,
    TenantLifecycleError,
    TenantResolutionError,
    TenantValidationError,
)


def make_tenant(status: TenantStatus = TenantStatus.ACTIVE) -> Tenant:
    """Build a deterministic reference tenant."""
    return Tenant("tenant-1", "Example", "example", "org-1", status, region="local")


def test_model_context_and_factory_are_explicit_immutable_and_json_safe() -> None:
    tenant = TenantFactory.create(
        tenant_id=None,
        id_factory=lambda: "tenant-1",
        name="Example",
        slug="example",
        organization_id="org-1",
        metadata={"source": "test"},
    )
    context = system_tenant_context("tenant-1", "org-1")

    assert tenant.to_dict()["status"] == "active"
    assert context.user_id == "system"
    assert optional_tenant(None) is None
    with pytest.raises(TenantValidationError):
        require_tenant(TenantContext())
    with pytest.raises(FrozenInstanceError):
        tenant.name = "Changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        tenant.metadata["source"] = "other"  # type: ignore[index]


def test_registry_resolver_binding_and_membership_are_deterministic() -> None:
    tenant = make_tenant()
    registry = TenantRegistry()
    resolver = ReferenceTenantResolver({tenant.tenant_id: tenant})
    registry.register(tenant)

    assert registry.lookup_by_slug("example") is tenant
    assert registry.snapshot() == (tenant,)
    assert resolver.resolve(TenantContext("tenant-1", "org-1")) is tenant
    assert OrganizationTenantBinding("org-1", "tenant-1").tenant_id == "tenant-1"
    assert (
        TenantMembershipDescriptor("tenant-1", "member-1").membership_id == "member-1"
    )
    assert TenantAccessDescriptor("tenant-1", "user-1", {"read"}).requested_scopes == {
        "read"
    }
    assert TenantDescriptor("tenant-1", {"routing"}).capabilities == {"routing"}
    with pytest.raises(TenantConflictError):
        registry.register(tenant)
    with pytest.raises(TenantResolutionError):
        resolver.resolve(TenantContext("tenant-1", "wrong-org"))


def test_isolation_routing_and_quota_are_descriptors_not_enforcement() -> None:
    isolation = TenantIsolationDescriptor(TenantIsolationMode.LOGICAL)
    decision = TenantIsolationDecision(
        TenantIsolationMode.LOGICAL, TenantIsolationMode.LOGICAL, "reference", isolation
    )
    route = TenantRoute(region="local", namespace="tenant-1")
    routing = ReferenceTenantRoutingPolicy({"tenant-1": route})
    quotas = ReferenceTenantQuotaService(
        {
            "tenant-1": TenantQuota(
                "tenant-1",
                (TenantQuotaLimit("requests", 10),),
                (TenantQuotaUsage("requests", 4),),
            )
        }
    )

    assert decision.effective_mode is TenantIsolationMode.LOGICAL
    assert routing.route(TenantRoutingRequest(TenantContext("tenant-1"))).route == route
    assert quotas.check("tenant-1", "requests").remaining == 6


def test_lifecycle_and_policy_remain_reference_only() -> None:
    lifecycle = ReferenceTenantLifecycle((make_tenant(TenantStatus.PROVISIONED),))
    active = lifecycle.transition("tenant-1", TenantLifecycleState.ACTIVATE)
    assert active.status is TenantStatus.ACTIVE
    assert lifecycle.events()[0].current_status is TenantStatus.ACTIVE
    with pytest.raises(TenantLifecycleError):
        lifecycle.transition("tenant-1", TenantLifecycleState.PROVISION)
    assert not ReferenceTenantPolicy().validate_context(TenantContext()).valid


def test_reference_provision_and_named_quota_resources_are_declarative() -> None:
    lifecycle = ReferenceTenantLifecycle()

    provisioned = lifecycle.provision(make_tenant())

    assert provisioned.status is TenantStatus.PROVISIONED
    assert TenantQuotaResource.MEMORY_RECORDS.value == "memory_records"


def test_registry_concurrent_registration_has_a_stable_immutable_snapshot() -> None:
    registry = TenantRegistry()

    def register(index: int) -> None:
        tenant_id = f"tenant-{index}"
        registry.register(Tenant(tenant_id, tenant_id, tenant_id, "org-1"))

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(register, range(8)))

    snapshot = registry.snapshot()
    assert [tenant.tenant_id for tenant in snapshot] == sorted(
        tenant.tenant_id for tenant in snapshot
    )
    assert len(snapshot) == 8


def test_documentation_declares_no_tenant_security_or_persistence() -> None:
    document = (
        __import__("pathlib").Path(__file__).parents[3] / "docs" / "Tenant.md"
    ).read_text(encoding="utf-8")
    assert "No real tenant isolation" in document
    assert "No tenant authentication" in document
