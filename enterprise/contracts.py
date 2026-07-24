"""Enterprise service Protocols reserved for future explicitly injected adapters."""

from __future__ import annotations

from typing import Protocol

from .models import (
    AuditEvent,
    LicenseDescriptor,
    Organization,
    Permission,
    Role,
    Tenant,
    User,
)


class OrganizationDirectory(Protocol):
    """Future organization/workspace/team directory boundary."""

    def get_organization(self, organization_id: str) -> Organization: ...
    def list_users(self, organization_id: str) -> tuple[User, ...]: ...
    def list_roles(self, organization_id: str) -> tuple[Role, ...]: ...


class TenantDirectory(Protocol):
    """Future tenant isolation and quota declaration boundary."""

    def get_tenant(self, tenant_id: str) -> Tenant: ...
    def list_tenants(self, organization_id: str) -> tuple[Tenant, ...]: ...


class IdentityProvider(Protocol):
    """Future OIDC/OAuth2/SAML/LDAP/JWT adapter boundary, with no login flow."""

    def subject(self, token_or_assertion: object) -> User: ...


class AuthorizationService(Protocol):
    """Future RBAC decision boundary with an ABAC extension point in context."""

    def permissions_for(self, user: User, tenant: Tenant) -> tuple[Permission, ...]: ...
    def allows(self, user: User, tenant: Tenant, permission: Permission) -> bool: ...


class AuditLogService(Protocol):
    """Future append/query boundary for immutable compliance audit events."""

    def append(self, event: AuditEvent) -> None: ...
    def list_events(self, tenant_id: str) -> tuple[AuditEvent, ...]: ...


class LicenseService(Protocol):
    """Future edition/entitlement lookup boundary without enforcement logic."""

    def license_for(self, organization_id: str) -> LicenseDescriptor: ...
