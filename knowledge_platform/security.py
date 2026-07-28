"""Mandatory security boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Scope


@dataclass(frozen=True, slots=True)
class SecurityPolicy:
    max_file_size: int = 25 * 1024 * 1024
    max_documents: int = 10_000
    max_top_k: int = 100
    allowed_content_types: frozenset[str] = frozenset(
        {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown",
            "text/html",
            "text/csv",
            "application/json",
        }
    )
    sensitive_metadata: frozenset[str] = frozenset(
        {"authorization", "cookie", "password", "secret", "token", "api_key"}
    )

    def validate_file(self, content_type: str, size: int) -> None:
        if content_type not in self.allowed_content_types:
            raise ValueError("Content type is not allowed.")
        if size < 0 or size > self.max_file_size:
            raise ValueError("File size limit exceeded.")

    def validate_top_k(self, top_k: int) -> None:
        if not 1 <= top_k <= self.max_top_k:
            raise ValueError("Top K limit exceeded.")

    def redact(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            key: "[REDACTED]" if key.lower() in self.sensitive_metadata else value
            for key, value in metadata.items()
        }


def enforce_scope(requested: Scope, resource: Scope) -> None:
    if requested != resource:
        raise PermissionError("Tenant, workspace, or namespace isolation violation.")
