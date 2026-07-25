"""Serializable Workspace graph projections with no graph database dependency."""

from __future__ import annotations

from dataclasses import dataclass

from ..models import Workspace
from .models import Membership


@dataclass(frozen=True, slots=True)
class WorkspaceGraphSnapshot:
    """Stable, immutable nodes and membership edges for one workspace."""

    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe graph representation."""
        return {"nodes": list(self.nodes), "edges": [list(edge) for edge in self.edges]}


class WorkspaceGraph:
    """Build a small reference graph from explicit workspace membership data."""

    @staticmethod
    def snapshot(
        workspace: Workspace, memberships: tuple[Membership, ...]
    ) -> WorkspaceGraphSnapshot:
        """Project account/workspace/principal relationships in stable order."""
        nodes = (workspace.account_id, workspace.workspace_id) + tuple(
            membership.principal_id
            for membership in sorted(memberships, key=lambda item: item.principal_id)
        )
        edges = ((workspace.account_id, workspace.workspace_id),) + tuple(
            (workspace.workspace_id, membership.principal_id)
            for membership in sorted(memberships, key=lambda item: item.principal_id)
        )
        return WorkspaceGraphSnapshot(nodes, edges)
