"""Offline RC-1 integration validation across Enterprise Foundation layers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from enterprise.audit import (
    AuditActor,
    AuditActorKind,
    AuditCategory,
    AuditContext,
    AuditEvent,
    AuditOutcome,
    AuditOutcomeStatus,
    AuditTarget,
    AuditTargetKind,
    ReferenceAuditService,
)
from enterprise.audit.errors import AuditClosedError
from enterprise.audit.mapping import actor_from_identity, context_from_tenant
from enterprise.authorization import (
    ActionDescriptor,
    AuthorizationContext,
    AuthorizationOutcome,
    AuthorizationRequest,
    PermissionDescriptor,
    ReferenceAuthorizationService,
    ResourceDescriptor,
    RoleDescriptor,
)
from enterprise.identity import (
    IdentityDescriptor,
    IdentityKind,
    IdentityPrincipal,
    ReferenceIdentityProvider,
)
from enterprise.license import Edition, LicenseEntitlement, ReferenceLicenseService
from enterprise.organization import OrganizationContext
from enterprise.tenant import ReferenceTenantResolver, Tenant, TenantContext


def test_enterprise_reference_chain_is_explicit_offline_and_deterministic() -> None:
    principal = IdentityPrincipal(
        "user-1", IdentityKind.USER, "User", role_ids={"viewer"}
    )
    identity = ReferenceIdentityProvider(
        IdentityDescriptor("reference", {IdentityKind.USER}), {"user-1": principal}
    )
    tenant = Tenant("tenant-1", "Tenant", "tenant", "org-1")
    tenant_context = TenantContext("tenant-1", "org-1", user_id="user-1")
    resolver = ReferenceTenantResolver({"tenant-1": tenant})
    permission = PermissionDescriptor(
        "workflow.read", ResourceDescriptor("workflow"), ActionDescriptor("read")
    )
    authorization = ReferenceAuthorizationService(
        {"viewer": RoleDescriptor("viewer", "Viewer", {"workflow.read"})}
    )
    audit = ReferenceAuditService()
    license_service = ReferenceLicenseService(
        (LicenseEntitlement("license-1", Edition.ENTERPRISE),)
    )

    assert identity.resolve("user-1") is principal
    assert OrganizationContext("org-1").organization_id == "org-1"
    assert resolver.resolve(tenant_context) is tenant
    decision = authorization.evaluate(
        AuthorizationRequest(AuthorizationContext("user-1", {"viewer"}), permission)
    )
    assert decision.outcome is AuthorizationOutcome.ALLOWED
    audit.record(
        AuditEvent(
            "event-1",
            datetime.now(timezone.utc),
            "read",
            AuditCategory.AUTHORIZATION,
            actor_from_identity(principal),
            AuditTarget("workflow-1", AuditTargetKind.WORKFLOW, "Workflow"),
            AuditOutcome(AuditOutcomeStatus.SUCCESS),
            context_from_tenant(tenant_context),
        )
    )
    assert audit.snapshot()[0].event_id == "event-1"
    assert license_service.get("license-1").edition is Edition.ENTERPRISE


def test_lifecycle_and_failure_isolation_do_not_contaminate_other_components() -> None:
    audit = ReferenceAuditService()
    audit.close()
    with pytest.raises(AuditClosedError):
        audit.record(
            AuditEvent(
                "event-1",
                datetime.now(timezone.utc),
                "read",
                AuditCategory.SYSTEM,
                AuditActor("system", AuditActorKind.SYSTEM, "System"),
                AuditTarget("system", AuditTargetKind.SYSTEM, "System"),
                AuditOutcome(AuditOutcomeStatus.SUCCESS),
                AuditContext(),
            )
        )

    authorization = ReferenceAuthorizationService({})
    request = AuthorizationRequest(
        AuthorizationContext("user-1"),
        PermissionDescriptor(
            "workflow.read", ResourceDescriptor("workflow"), ActionDescriptor("read")
        ),
    )
    assert authorization.evaluate(request).outcome is AuthorizationOutcome.INDETERMINATE
