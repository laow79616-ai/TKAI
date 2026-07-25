"""Offline regression tests for the Enterprise architecture contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import get_type_hints

import pytest

from enterprise import (
    AuditLogService,
    AuthorizationService,
    DeploymentProfile,
    IdentityProvider,
    LicenseService,
    Organization,
    OrganizationDirectory,
    Permission,
    Role,
    Tenant,
    TenantDirectory,
)
from enterprise.models import (
    AuditEvent,
    AuditOperation,
    DeploymentMode,
    IdentityProtocol,
    LicenseDescriptor,
    LicenseEdition,
    Quota,
)


def test_organization_and_tenant_descriptors_are_immutable() -> None:
    """Architecture descriptors defensively freeze values without persistence."""
    source_metadata = {"region": "local"}
    organization = Organization("org-1", "Example", source_metadata)
    tenant = Tenant(
        "tenant-1",
        organization.organization_id,
        "Example tenant",
        quotas=(Quota("requests", 10, "requests"),),
        metadata=source_metadata,
    )

    source_metadata["region"] = "changed"

    assert organization.metadata == {"region": "local"}
    assert tenant.quotas[0].limit == 10
    with pytest.raises(TypeError):
        organization.metadata["region"] = "other"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        tenant.name = "changed"  # type: ignore[misc]


def test_enterprise_models_cover_documented_architecture_domains() -> None:
    """License, identity, audit, and deployment are descriptors, not services."""
    license_descriptor = LicenseDescriptor(
        LicenseEdition.ENTERPRISE, "org-1", {"audit", "rbac"}
    )
    event = AuditEvent(
        "event-1",
        "tenant-1",
        "user-1",
        AuditOperation.EXECUTE,
        "workflow:demo",
    )
    profile = DeploymentProfile(DeploymentMode.HIGH_AVAILABILITY, replicas=3)

    assert IdentityProtocol.OIDC.value == "oidc"
    assert license_descriptor.features == frozenset({"audit", "rbac"})
    assert event.operation is AuditOperation.EXECUTE
    assert profile.mode is DeploymentMode.HIGH_AVAILABILITY


def test_service_contracts_are_importable_without_implementations() -> None:
    """The architecture exposes Protocols only and creates no runtime services."""
    contracts = (
        OrganizationDirectory,
        TenantDirectory,
        IdentityProvider,
        AuthorizationService,
        AuditLogService,
        LicenseService,
    )

    assert all(getattr(contract, "_is_protocol", False) for contract in contracts)
    assert "organization_id" in get_type_hints(Organization)
    assert "resource" in get_type_hints(Permission)
    assert "permission_ids" in get_type_hints(Role)


def test_enterprise_documentation_declares_architecture_only_scope() -> None:
    """Documentation keeps unimplemented enterprise capabilities unambiguous."""
    document = (
        __import__("pathlib").Path(__file__).parents[2] / "docs" / "Enterprise.md"
    ).read_text(encoding="utf-8")

    for heading in (
        "## Architecture",
        "## Organization",
        "## Multi-tenant",
        "## Authorization",
        "## License",
        "## Deployment",
        "## Roadmap",
    ):
        assert heading in document
    assert "No database" in document
    assert "No login" in document
