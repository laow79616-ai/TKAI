"""Enterprise Features Foundation; explicit, offline, and reference-first."""

from .models import (
    ApiKeyId,
    ApiKeyRecord,
    AuditAction,
    AuditEvent,
    OrganizationId,
    OrganizationRecord,
    RoleAssignment,
    RoleId,
    RoleRecord,
    TeamId,
    TeamRecord,
    UserId,
    UserRecord,
)
from .permissions import AuthorizationService, builtin_roles
from .service import PBKDF2PasswordHasher, ReferenceEnterpriseService
from .storage import EnterpriseStorage, ReferenceEnterpriseStorage

__all__ = (
    "AuthorizationService",
    "ApiKeyId",
    "ApiKeyRecord",
    "AuditAction",
    "AuditEvent",
    "EnterpriseStorage",
    "PBKDF2PasswordHasher",
    "ReferenceEnterpriseService",
    "ReferenceEnterpriseStorage",
    "OrganizationId",
    "OrganizationRecord",
    "RoleAssignment",
    "RoleId",
    "RoleRecord",
    "TeamId",
    "TeamRecord",
    "UserId",
    "UserRecord",
    "builtin_roles",
)
