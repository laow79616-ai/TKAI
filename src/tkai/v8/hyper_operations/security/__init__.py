"""RBAC-compatible isolation and recursive secret filtering."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.hyper_operations.contracts import OperationsScope, immutable_metadata

_SECRET_MARKERS = ("secret", "password", "token", "api_key", "credential", "cookie")


def _filter(value: object) -> object:
    if isinstance(value, Mapping):
        return immutable_metadata(
            {
                str(key): "[REDACTED]"
                if any(marker in str(key).lower() for marker in _SECRET_MARKERS)
                else _filter(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, (list, tuple)):
        return tuple(_filter(item) for item in value)
    return value


def secure_metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    result = _filter(values)
    if not isinstance(result, Mapping):
        raise TypeError("metadata must be a mapping")
    return result


@dataclass(frozen=True)
class OperationsPrincipal:
    principal_id: str
    roles: frozenset[str] = frozenset({"operations-reader"})
    tenant: str = "default"
    workspace: str = "default"
    operations: str = "default"


class OperationsAccessController:
    def authorize(
        self, principal: OperationsPrincipal, permission: str, scope: OperationsScope
    ) -> None:
        if permission != "operations:read":
            raise PermissionError("Hyper Operations only supports operations:read")
        if principal.tenant != scope.tenant:
            raise PermissionError("tenant isolation boundary violation")
        if principal.workspace != scope.workspace:
            raise PermissionError("workspace isolation boundary violation")
        if principal.operations != scope.operations:
            raise PermissionError("operations isolation boundary violation")
        if not principal.roles.intersection(
            {"operations-reader", "operations-reviewer", "operations-admin"}
        ):
            raise PermissionError("RBAC role does not permit operations metadata read")


__all__ = ("OperationsAccessController", "OperationsPrincipal", "secure_metadata")
