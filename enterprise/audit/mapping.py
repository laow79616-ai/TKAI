"""Pure mapping helpers that never record events or mutate source descriptors."""

from __future__ import annotations

from ..authorization.models import AuthorizationDecision, AuthorizationOutcome
from ..identity.models import IdentityPrincipal
from ..tenant.context import TenantContext
from .models import (
    AuditActor,
    AuditActorKind,
    AuditContext,
    AuditOutcome,
    AuditOutcomeStatus,
    AuditTarget,
    AuditTargetKind,
)


def actor_from_identity(principal: IdentityPrincipal) -> AuditActor:
    return AuditActor(
        principal.principal_id,
        AuditActorKind(principal.kind.value),
        principal.display_name,
    )


def context_from_tenant(context: TenantContext) -> AuditContext:
    return AuditContext(
        context.tenant_id,
        context.organization_id,
        context.workspace_id,
        context.user_id,
        context.user_id,
        context.request_id,
        context.correlation_id,
    )


def outcome_from_authorization(decision: AuthorizationDecision) -> AuditOutcome:
    status = (
        AuditOutcomeStatus.SUCCESS
        if decision.outcome is AuthorizationOutcome.ALLOWED
        else AuditOutcomeStatus.DENIED
    )
    return AuditOutcome(status, "; ".join(decision.explanation.reasons) or None)


def target_from_descriptor(
    identifier: str, name: str, kind: AuditTargetKind
) -> AuditTarget:
    return AuditTarget(identifier, kind, name)
