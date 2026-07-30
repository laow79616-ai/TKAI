"""RBAC, isolation, and secret filtering for planning metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.hyper_planning.contracts import PlanningScope

_SECRET_MARKERS = ("api_key", "secret", "token", "password", "credential")


def secure_metadata(values: Mapping[str, object]) -> dict[str, object]:
    secured: dict[str, object] = {}
    for key, value in values.items():
        if any(marker in str(key).lower() for marker in _SECRET_MARKERS):
            secured[str(key)] = "[REDACTED]"
        elif isinstance(value, Mapping):
            secured[str(key)] = secure_metadata(value)
        else:
            secured[str(key)] = value
    return secured


@dataclass(frozen=True)
class PlanningPrincipal:
    subject: str
    roles: frozenset[str] = frozenset({"planning:read"})
    tenant: str = "default"
    workspace: str = "default"
    planning_namespaces: frozenset[str] = frozenset({"default"})


class PlanningAccessController:
    def authorize(
        self, principal: PlanningPrincipal, permission: str, scope: PlanningScope
    ) -> None:
        if permission not in principal.roles:
            raise PermissionError("planning permission denied")
        if principal.tenant != scope.tenant or principal.workspace != scope.workspace:
            raise PermissionError("planning tenant or workspace isolation violation")
        if (
            "*" not in principal.planning_namespaces
            and scope.planning_namespace not in principal.planning_namespaces
        ):
            raise PermissionError("planning namespace isolation violation")


__all__ = ("PlanningAccessController", "PlanningPrincipal", "secure_metadata")
