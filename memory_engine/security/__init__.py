"""Tenant/workspace isolation, RBAC, secret references, encryption, and audit."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Protocol

from ..models import MemoryObject, MemoryScope


class EncryptionProvider(Protocol):
    def encrypt(self, value: bytes, reference: str) -> bytes: ...

    def decrypt(self, value: bytes, reference: str) -> bytes: ...


class MemorySecurity:
    def __init__(self, encryption: EncryptionProvider | None = None) -> None:
        self.encryption = encryption
        self._grants: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        self.audit: list[dict[str, Any]] = []

    def grant(self, scope: MemoryScope, permissions: set[str]) -> None:
        self._grants[(scope.tenant, scope.workspace, scope.owner)].update(permissions)

    def require(self, scope: MemoryScope, permission: str) -> None:
        key = (scope.tenant, scope.workspace, scope.owner)
        if permission not in self._grants[key]:
            raise PermissionError(f"{permission} is required.")
        self.record(scope, permission)

    def isolate(self, scope: MemoryScope, memory: MemoryObject) -> None:
        if memory.tenant != scope.tenant:
            raise PermissionError("Cross-tenant memory access is denied.")
        if memory.workspace != scope.workspace:
            raise PermissionError("Cross-workspace memory access is denied.")
        if memory.owner != scope.owner and memory.type.value != "shared":
            raise PermissionError("Memory owner access is denied.")

    def validate_secrets(self, value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if "secret" in key.lower() and not (
                    isinstance(item, str) and item.startswith("secret://")
                ):
                    raise ValueError("Secrets must use secret:// references.")
                self.validate_secrets(item)
        elif isinstance(value, list):
            for item in value:
                self.validate_secrets(item)

    def record(self, scope: MemoryScope, action: str, **details: Any) -> None:
        self.audit.append(
            {
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "owner": scope.owner,
                "action": action,
                **details,
            }
        )
