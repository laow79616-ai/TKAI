"""Credential-reference and log-safety boundaries."""

from __future__ import annotations

from typing import Protocol


class SecretResolver(Protocol):
    def exists(self, reference: str, tenant: str, workspace: str) -> bool: ...


class ReferenceSecretResolver:
    """Test-safe resolver that retains references only, never secret material."""

    def __init__(self, references: set[tuple[str, str, str]] | None = None) -> None:
        self.references = references or set()

    def exists(self, reference: str, tenant: str, workspace: str) -> bool:
        return not reference or (tenant, workspace, reference) in self.references


def sanitized_metadata(metadata: dict[str, object]) -> dict[str, object]:
    blocked = ("password", "username", "secret", "token", "credential", "cookie")
    return {
        key: value
        for key, value in metadata.items()
        if not any(item in key.casefold() for item in blocked)
    }
