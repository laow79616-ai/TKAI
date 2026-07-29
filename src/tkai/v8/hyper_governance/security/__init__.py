"""RBAC-compatible isolation and secret filtering."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.hyper_governance.contracts import (
    GovernanceScope,
    immutable_metadata,
)

_SECRET_MARKERS = ("secret", "password", "token", "api_key", "credential")


def secure_metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    """Redact common secret-bearing keys from metadata projections."""

    filtered = {
        key: (
            "[REDACTED]"
            if any(marker in key.lower() for marker in _SECRET_MARKERS)
            else value
        )
        for key, value in values.items()
    }
    return immutable_metadata(filtered)


@dataclass(frozen=True)
class GovernancePrincipal:
    """Read-only principal compatible with RBAC identity projections."""

    principal_id: str
    roles: frozenset[str] = frozenset({"governance-reader"})
    tenant: str = "default"
    workspace: str = "default"


class GovernanceAccessController:
    """Validate read scope without granting runtime capabilities."""

    def authorize(
        self,
        principal: GovernancePrincipal,
        permission: str,
        scope: GovernanceScope,
    ) -> None:
        if permission != "governance:read":
            raise PermissionError("Hyper Governance only supports governance:read")
        if scope.tenant != principal.tenant:
            raise PermissionError("tenant isolation boundary violation")
        if scope.workspace != principal.workspace:
            raise PermissionError("workspace isolation boundary violation")
        if not principal.roles.intersection(
            {"governance-reader", "governance-reviewer", "governance-admin"}
        ):
            raise PermissionError("RBAC role does not permit governance metadata read")


__all__ = (
    "GovernanceAccessController",
    "GovernancePrincipal",
    "secure_metadata",
)
