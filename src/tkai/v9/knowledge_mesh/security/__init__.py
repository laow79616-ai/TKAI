"""RBAC-compatible isolation and secret filtering for knowledge reads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.security import filter_secrets
from tkai.v9.knowledge_mesh.contracts import KnowledgeScope


@dataclass(frozen=True)
class KnowledgePrincipal:
    identifier: str
    roles: frozenset[str] = frozenset({"knowledge_viewer"})
    tenant: str = "default"
    workspace: str = "default"
    knowledge_namespaces: frozenset[str] = frozenset({"*"})


class KnowledgeAccessController:
    ROLE_PERMISSIONS = {
        "knowledge_viewer": frozenset({"knowledge:read"}),
        "knowledge_auditor": frozenset({"knowledge:read", "knowledge:audit:read"}),
        "administrator": frozenset({"*"}),
    }

    def authorize(
        self,
        principal: KnowledgePrincipal,
        permission: str,
        scope: KnowledgeScope,
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
        raise TypeError("filtered knowledge metadata must remain a mapping")
    return filtered


__all__ = (
    "KnowledgeAccessController",
    "KnowledgePrincipal",
    "filter_secrets",
    "secure_metadata",
)
