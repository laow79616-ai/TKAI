"""Isolation, redaction and read-only authorization for recovery metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from tkai.v8.hyper_recovery.contracts import RecoveryScope

SECRET_MARKERS = (
    "password",
    "secret",
    "token",
    "cookie",
    "session",
    "api_key",
    "proxy",
)


def secure_metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    cleaned: dict[str, object] = {}
    for key, value in values.items():
        lowered = str(key).lower()
        if any(marker in lowered for marker in SECRET_MARKERS):
            cleaned[str(key)] = "[REDACTED]"
        elif isinstance(value, Mapping):
            cleaned[str(key)] = secure_metadata(value)
        else:
            cleaned[str(key)] = value
    return MappingProxyType(cleaned)


@dataclass(frozen=True)
class RecoveryPrincipal:
    subject: str
    roles: frozenset[str] = frozenset({"recovery-reader"})
    tenant: str = "default"
    workspace: str = "default"
    namespace: str = "default"
    profile: str = "default"


def authorize_read(principal: RecoveryPrincipal, scope: RecoveryScope) -> None:
    if not principal.roles.intersection(
        {"recovery-reader", "recovery-reviewer", "recovery-admin"}
    ):
        raise PermissionError("RBAC role does not permit recovery metadata read")
    if (
        principal.tenant,
        principal.workspace,
        principal.namespace,
        principal.profile,
    ) != (scope.tenant, scope.workspace, scope.namespace, scope.profile):
        raise PermissionError("recovery isolation boundary violation")
