"""Offline Enterprise Authorization Foundation contracts and reference components."""

from .models import (
    ActionDescriptor,
    Attribute,
    AuthorizationCapability,
    AuthorizationContext,
    AuthorizationDecision,
    AuthorizationExplanation,
    AuthorizationOutcome,
    AuthorizationRequest,
    Environment,
    PermissionDescriptor,
    Resource,
    ResourceDescriptor,
    RoleDescriptor,
    ScopeDescriptor,
    Subject,
)
from .registry import ReferencePermissionRegistry, ReferenceRoleRegistry
from .service import (
    AuthorizationPolicy,
    AuthorizationService,
    PolicyExpression,
    ReferenceAuthorizationService,
)

__all__ = (
    "ActionDescriptor",
    "Attribute",
    "AuthorizationCapability",
    "AuthorizationContext",
    "AuthorizationDecision",
    "AuthorizationExplanation",
    "AuthorizationOutcome",
    "AuthorizationPolicy",
    "AuthorizationRequest",
    "AuthorizationService",
    "Environment",
    "PermissionDescriptor",
    "PolicyExpression",
    "ReferenceAuthorizationService",
    "ReferencePermissionRegistry",
    "ReferenceRoleRegistry",
    "Resource",
    "ResourceDescriptor",
    "RoleDescriptor",
    "ScopeDescriptor",
    "Subject",
)
