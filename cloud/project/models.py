"""Workspace/project relationships as immutable declarations only."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..models import CloudValue, snapshot


@dataclass(frozen=True, slots=True)
class WorkspaceProjectBinding:
    """Declares that a project belongs to one explicit workspace."""

    workspace_id: str
    project_id: str
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.workspace_id or not self.project_id:
            raise ValueError("Workspace and project ids must not be empty.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class ProjectMembershipDescriptor:
    """Describes a project member without inheriting workspace permissions."""

    project_id: str
    principal_id: str
    role: str = "member"
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.project_id or not self.principal_id:
            raise ValueError("Project and principal ids must not be empty.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class ProjectHierarchy:
    """Serializable workspace-to-project hierarchy snapshot."""

    workspace_id: str
    project_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("Project hierarchy requires a workspace id.")
        object.__setattr__(self, "project_ids", tuple(sorted(self.project_ids)))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe hierarchy snapshot."""
        return {
            "workspace_id": self.workspace_id,
            "project_ids": list(self.project_ids),
        }
