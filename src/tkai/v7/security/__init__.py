"""Compatibility-focused security boundaries for V7 modules."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

_SECRET_MARKERS = (
    "secret",
    "password",
    "token",
    "api_key",
    "apikey",
    "credential",
)


def filter_secrets(values: Mapping[str, object]) -> dict[str, object]:
    """Recursively redact values whose keys indicate secret material."""
    filtered: dict[str, object] = {}
    for key, value in values.items():
        if any(marker in key.lower() for marker in _SECRET_MARKERS):
            filtered[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            filtered[key] = filter_secrets(value)
        else:
            filtered[key] = value
    return filtered


@dataclass(frozen=True)
class Principal:
    """V7 principal compatible with role-based authorization."""

    identifier: str
    roles: frozenset[str] = frozenset()


class AccessController:
    """Deny-by-default RBAC checker."""

    def __init__(self, grants: Mapping[str, Iterable[str]] | None = None) -> None:
        self._grants = {
            role: frozenset(capabilities)
            for role, capabilities in (grants or {}).items()
        }

    def allowed(self, principal: Principal, capability: str) -> bool:
        return any(
            capability in self._grants.get(role, frozenset())
            for role in principal.roles
        )

    def require(self, principal: Principal, capability: str) -> None:
        if not self.allowed(principal, capability):
            raise PermissionError(
                f"principal {principal.identifier!r} lacks {capability!r}"
            )


class IsolationPolicy:
    """Restricts each module to an explicitly granted capability set."""

    def __init__(self) -> None:
        self._grants: dict[str, frozenset[str]] = {}

    def grant(self, module: str, capabilities: Iterable[str]) -> None:
        self._grants[module] = frozenset(capabilities)

    def require(self, module: str, capability: str) -> None:
        if capability not in self._grants.get(module, frozenset()):
            raise PermissionError(
                f"module {module!r} is isolated from capability {capability!r}"
            )


__all__ = (
    "AccessController",
    "IsolationPolicy",
    "Principal",
    "filter_secrets",
)
