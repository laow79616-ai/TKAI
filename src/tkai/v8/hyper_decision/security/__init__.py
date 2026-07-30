"""RBAC-compatible tenant, workspace, and decision isolation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.hyper_decision.contracts import DecisionScope
from tkai.v8.security import filter_secrets


@dataclass(frozen=True)
class DecisionPrincipal:
    identifier: str
    roles: frozenset[str] = frozenset({"decision_viewer"})
    tenant: str = "default"
    workspace: str = "default"
    decision_namespaces: frozenset[str] = frozenset({"*"})


class DecisionAccessController:
    ROLE_PERMISSIONS = {
        "decision_viewer": frozenset({"decision:read"}),
        "decision_reviewer": frozenset({"decision:read", "decision:review:read"}),
        "decision_auditor": frozenset({"decision:read", "decision:audit:read"}),
        "administrator": frozenset({"*"}),
    }

    def authorize(
        self, principal: DecisionPrincipal, permission: str, scope: DecisionScope
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
            "*" not in principal.decision_namespaces
            and scope.decision_namespace not in principal.decision_namespaces
        ):
            raise PermissionError("decision isolation")


def secure_metadata(value: Mapping[str, object]) -> Mapping[str, object]:
    filtered = filter_secrets(value)
    if not isinstance(filtered, Mapping):
        raise TypeError("filtered decision metadata must remain a mapping")
    return filtered


__all__ = ("DecisionAccessController", "DecisionPrincipal", "secure_metadata")
