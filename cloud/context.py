"""Explicit Cloud request scope with no ambient environment or identity lookup."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .models import CloudValue, snapshot


@dataclass(frozen=True, slots=True)
class CloudContext:
    """Caller-provided account, workspace, project, and correlation scope."""

    account_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    organization_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe context snapshot without resolving identifiers."""
        return {
            "account_id": self.account_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "organization_id": self.organization_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }
