"""Explicit Project request scope without global workspace or account resolution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..models import CloudValue, snapshot


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """Caller-provided project scope for reference-only project operations."""

    project_id: str | None = None
    workspace_id: str | None = None
    account_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe snapshot without any implicit lookup."""
        return {
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "account_id": self.account_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }
