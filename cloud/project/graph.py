"""Stable Project graph projections without a graph database or scheduler."""

from __future__ import annotations

from dataclasses import dataclass

from ..models import Project
from .models import ProjectMembershipDescriptor, WorkspaceProjectBinding


@dataclass(frozen=True, slots=True)
class ProjectGraphSnapshot:
    """Immutable workspace/project/principal graph snapshot."""

    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe graph representation."""
        return {
            "nodes": list(self.nodes),
            "edges": [list(edge) for edge in self.edges],
        }


class ProjectGraph:
    """Build a deterministic graph from explicit project declarations."""

    @staticmethod
    def snapshot(
        project: Project,
        binding: WorkspaceProjectBinding,
        memberships: tuple[ProjectMembershipDescriptor, ...],
    ) -> ProjectGraphSnapshot:
        """Project explicit relationships without workspace permission inheritance."""
        if binding.project_id != project.project_id:
            raise ValueError("Project graph binding must match the project id.")
        principals = tuple(
            membership.principal_id
            for membership in sorted(memberships, key=lambda item: item.principal_id)
            if membership.project_id == project.project_id
        )
        return ProjectGraphSnapshot(
            (binding.workspace_id, project.project_id) + principals,
            ((binding.workspace_id, project.project_id),)
            + tuple((project.project_id, principal) for principal in principals),
        )
