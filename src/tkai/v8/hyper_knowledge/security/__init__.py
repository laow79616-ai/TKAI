"""RBAC-compatible knowledge isolation and recursive secret filtering."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.hyper_knowledge.contracts import KnowledgeScope, immutable_metadata

_SECRET_MARKERS = ("secret", "password", "token", "api_key", "credential", "payload")


def _filter(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if any(marker in str(key).lower() for marker in _SECRET_MARKERS)
                else _filter(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return tuple(_filter(item) for item in value)
    return value


def secure_metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    return immutable_metadata(_filter(values))  # type: ignore[arg-type]


@dataclass(frozen=True)
class KnowledgePrincipal:
    principal_id: str
    roles: frozenset[str] = frozenset({"knowledge-reader"})
    tenant: str = "default"
    workspace: str = "default"
    knowledge: str = "*"


class KnowledgeAccessController:
    def authorize(
        self,
        principal: KnowledgePrincipal,
        permission: str,
        scope: KnowledgeScope,
    ) -> None:
        if permission != "knowledge:read":
            raise PermissionError("Hyper Knowledge only supports knowledge:read")
        if scope.tenant != principal.tenant:
            raise PermissionError("tenant isolation boundary violation")
        if scope.workspace != principal.workspace:
            raise PermissionError("workspace isolation boundary violation")
        if principal.knowledge != "*" and scope.knowledge != principal.knowledge:
            raise PermissionError("knowledge isolation boundary violation")
        if not principal.roles.intersection(
            {"knowledge-reader", "knowledge-reviewer", "knowledge-admin"}
        ):
            raise PermissionError("RBAC role does not permit knowledge metadata read")


__all__ = ("KnowledgeAccessController", "KnowledgePrincipal", "secure_metadata")
