"""Security boundary, RBAC isolation, and secret filtering."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.hyper_simulation.contracts import SimulationScope

_SECRET_MARKERS = (
    "api_key",
    "secret",
    "token",
    "password",
    "credential",
    "cookie",
    "session",
    "proxy",
)


def secure_metadata(values: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values.items():
        if any(marker in str(key).lower() for marker in _SECRET_MARKERS):
            result[str(key)] = "[REDACTED]"
        elif isinstance(value, Mapping):
            result[str(key)] = secure_metadata(value)
        else:
            result[str(key)] = value
    return result


@dataclass(frozen=True)
class SimulationPrincipal:
    subject: str
    roles: frozenset[str] = frozenset({"simulation:read"})
    tenant: str = "default"
    workspace: str = "default"
    namespaces: frozenset[str] = frozenset({"default"})
    profiles: frozenset[str] = frozenset({"*"})


class SimulationAccessController:
    def authorize(
        self, principal: SimulationPrincipal, permission: str, scope: SimulationScope
    ) -> None:
        if permission not in principal.roles:
            raise PermissionError("simulation permission denied")
        if principal.tenant != scope.tenant or principal.workspace != scope.workspace:
            raise PermissionError("tenant or workspace isolation violation")
        if (
            "*" not in principal.namespaces
            and scope.namespace not in principal.namespaces
        ):
            raise PermissionError("namespace isolation violation")
        if "*" not in principal.profiles and scope.profile not in principal.profiles:
            raise PermissionError("profile isolation violation")


PlanningPrincipal = SimulationPrincipal
PlanningAccessController = SimulationAccessController
