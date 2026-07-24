"""Explicit workspace scope without ambient account, identity, or request state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..models import CloudValue, snapshot


@dataclass(frozen=True, slots=True)
class WorkspaceContext:
    """Caller-provided workspace and principal scope for reference services."""

    workspace_id: str | None = None
    account_id: str | None = None
    principal_id: str | None = None
    project_id: str | None = None
    request_id: str | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe snapshot without resolving any identifier."""
        return {
            "workspace_id": self.workspace_id,
            "account_id": self.account_id,
            "principal_id": self.principal_id,
            "project_id": self.project_id,
            "request_id": self.request_id,
            "metadata": dict(self.metadata),
        }
