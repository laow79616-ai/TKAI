"""Authorization service contracts and deterministic, reference-only evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from .models import (
    AuthorizationCapability,
    AuthorizationDecision,
    AuthorizationExplanation,
    AuthorizationOutcome,
    AuthorizationRequest,
    RoleDescriptor,
)


class PolicyExpression(Protocol):
    """ABAC extension contract that only describes an expression."""

    def describe(self) -> str: ...


class AuthorizationPolicy(Protocol):
    """Explicit policy contract; implementations must not install request hooks."""

    def evaluate(self, request: AuthorizationRequest) -> AuthorizationDecision: ...


class AuthorizationService(Protocol):
    """Explicit evaluator boundary, independent of Runtime, SDK, and Studio hooks."""

    def evaluate(self, request: AuthorizationRequest) -> AuthorizationDecision: ...
    def explain(self, request: AuthorizationRequest) -> AuthorizationExplanation: ...
    def evaluate_many(
        self, requests: tuple[AuthorizationRequest, ...]
    ) -> tuple[AuthorizationDecision, ...]: ...
    def capabilities(self) -> tuple[AuthorizationCapability, ...]: ...


class ReferenceAuthorizationService:
    """Reference-only RBAC descriptor evaluator; it never intercepts a request."""

    def __init__(self, roles: Mapping[str, RoleDescriptor]) -> None:
        self._roles = dict(roles)

    def evaluate(self, request: AuthorizationRequest) -> AuthorizationDecision:
        """Describe role-permission agreement from supplied request data only."""
        if not request.context.subject_id:
            return AuthorizationDecision(
                AuthorizationOutcome.NOT_APPLICABLE,
                AuthorizationExplanation(("subject id is required",)),
            )
        known_roles = [
            self._roles[role_id]
            for role_id in sorted(request.context.role_ids)
            if role_id in self._roles
        ]
        if not known_roles:
            return AuthorizationDecision(
                AuthorizationOutcome.INDETERMINATE,
                AuthorizationExplanation(("no declared roles",)),
            )
        if any(
            request.permission.permission_id in role.permission_ids
            for role in known_roles
        ):
            return AuthorizationDecision(
                AuthorizationOutcome.ALLOWED,
                AuthorizationExplanation(("reference role descriptor matched",)),
            )
        return AuthorizationDecision(
            AuthorizationOutcome.DENIED,
            AuthorizationExplanation(("reference role descriptors did not match",)),
        )

    def explain(self, request: AuthorizationRequest) -> AuthorizationExplanation:
        """Return the same stable explanation as an explicit evaluation."""
        return self.evaluate(request).explanation

    def evaluate_many(
        self, requests: tuple[AuthorizationRequest, ...]
    ) -> tuple[AuthorizationDecision, ...]:
        """Evaluate caller-provided requests in supplied deterministic order."""
        return tuple(self.evaluate(request) for request in requests)

    def capabilities(self) -> tuple[AuthorizationCapability, ...]:
        """Declare reference RBAC and ABAC-extension support without discovery."""
        return (
            AuthorizationCapability("reference_rbac"),
            AuthorizationCapability("abac_contracts"),
        )
