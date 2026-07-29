"""RBAC-compatible isolation and secret filtering for intelligence reads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.hyper_intelligence.contracts import IntelligenceScope
from tkai.v8.security import filter_secrets


@dataclass(frozen=True)
class IntelligencePrincipal:
    identifier: str
    roles: frozenset[str] = frozenset({"intelligence_viewer"})
    tenant: str = "default"
    workspace: str = "default"
    knowledge_namespaces: frozenset[str] = frozenset({"*"})


class IntelligenceAccessController:
    ROLE_PERMISSIONS = {
        "intelligence_viewer": frozenset({"intelligence:read"}),
        "intelligence_auditor": frozenset(
            {"intelligence:read", "intelligence:audit:read"}
        ),
        "administrator": frozenset({"*"}),
    }

    def authorize(
        self,
        principal: IntelligencePrincipal,
        permission: str,
        scope: IntelligenceScope,
    ) -> None:
        permissions = {
            item
            for role in principal.roles
            for item in self.ROLE_PERMISSIONS.get(role, frozenset())
        }
        if permission not in permissions and "*" not in permissions:
            raise PermissionError(permission)
        if principal.tenant != scope.tenant:
            raise PermissionError("tenant isolation")
        if principal.workspace != scope.workspace:
            raise PermissionError("workspace isolation")
        if (
            "*" not in principal.knowledge_namespaces
            and scope.knowledge_namespace not in principal.knowledge_namespaces
        ):
            raise PermissionError("knowledge isolation")


def secure_metadata(value: Mapping[str, object]) -> Mapping[str, object]:
    filtered = filter_secrets(value)
    if not isinstance(filtered, Mapping):
        raise TypeError("filtered intelligence metadata must remain a mapping")
    return filtered


__all__ = (
    "IntelligenceAccessController",
    "IntelligencePrincipal",
    "filter_secrets",
    "secure_metadata",
)
