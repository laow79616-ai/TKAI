"""RBAC-compatible isolation and secret filtering for reasoning reads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.hyper_reasoning.contracts import (
    ReasoningScope,
    reject_hidden_reasoning,
)
from tkai.v8.security import filter_secrets


@dataclass(frozen=True)
class ReasoningPrincipal:
    identifier: str
    roles: frozenset[str] = frozenset({"reasoning_viewer"})
    tenant: str = "default"
    workspace: str = "default"
    reasoning_namespaces: frozenset[str] = frozenset({"*"})


class ReasoningAccessController:
    ROLE_PERMISSIONS = {
        "reasoning_viewer": frozenset({"reasoning:read"}),
        "reasoning_auditor": frozenset(
            {"reasoning:read", "reasoning:audit:read"}
        ),
        "administrator": frozenset({"*"}),
    }

    def authorize(
        self,
        principal: ReasoningPrincipal,
        permission: str,
        scope: ReasoningScope,
    ) -> None:
        permissions = {
            permission
            for role in principal.roles
            for permission in self.ROLE_PERMISSIONS.get(role, frozenset())
        }
        if permission not in permissions and "*" not in permissions:
            raise PermissionError(permission)
        if principal.tenant != scope.tenant:
            raise PermissionError("tenant isolation")
        if principal.workspace != scope.workspace:
            raise PermissionError("workspace isolation")
        if (
            "*" not in principal.reasoning_namespaces
            and scope.reasoning_namespace not in principal.reasoning_namespaces
        ):
            raise PermissionError("reasoning isolation")


def secure_metadata(value: Mapping[str, object]) -> Mapping[str, object]:
    reject_hidden_reasoning(value)
    filtered = filter_secrets(value)
    if not isinstance(filtered, Mapping):
        raise TypeError("filtered reasoning metadata must remain a mapping")
    return filtered


__all__ = (
    "ReasoningAccessController",
    "ReasoningPrincipal",
    "secure_metadata",
)
