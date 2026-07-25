"""Explicit factory for immutable Project models without hidden configuration."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from ..models import CloudValue, Project, ProjectStatus


class ProjectFactory:
    """Create projects from explicit values supplied by the caller."""

    def create(
        self,
        project_id: str,
        workspace_id: str,
        name: str,
        *,
        slug: str | None = None,
        description: str = "",
        status: ProjectStatus = ProjectStatus.ACTIVE,
        tags: frozenset[str] = frozenset(),
        metadata: Mapping[str, CloudValue] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> Project:
        """Build a Project with explicit IDs and UTC timestamps."""
        now = datetime.now(timezone.utc)
        return Project(
            project_id,
            workspace_id,
            name,
            description,
            {} if metadata is None else metadata,
            slug,
            status,
            tags,
            now if created_at is None else created_at,
            now if updated_at is None else updated_at,
        )
