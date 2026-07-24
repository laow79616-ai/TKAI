"""In-memory reference Project service with no background work or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from ..models import CloudValue, Project, ProjectStatus
from .factory import ProjectFactory
from .models import ProjectMembershipDescriptor
from .registry import ProjectRegistry


class ReferenceProjectService:
    """Compose explicit registry and factory collaborators for local project use."""

    def __init__(
        self,
        registry: ProjectRegistry | None = None,
        factory: ProjectFactory | None = None,
    ) -> None:
        self._registry = registry if registry is not None else ProjectRegistry()
        self._factory = factory if factory is not None else ProjectFactory()

    @property
    def registry(self) -> ProjectRegistry:
        """Expose the explicit local registry for caller-owned lifecycle control."""
        return self._registry

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
        """Create and locally register one explicit reference project."""
        project = self._factory.create(
            project_id,
            workspace_id,
            name,
            slug=slug,
            description=description,
            status=status,
            tags=tags,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at,
        )
        return self._registry.register(project)

    def project(self, project_id: str) -> Project:
        """Return one local project snapshot."""
        return self._registry.get(project_id)

    def projects(self, workspace_id: str | None = None) -> tuple[Project, ...]:
        """Return local project snapshots in stable order."""
        return self._registry.list(workspace_id)

    def add_membership(
        self, membership: ProjectMembershipDescriptor
    ) -> ProjectMembershipDescriptor:
        """Record a project membership without resolving workspace permissions."""
        return self._registry.add_membership(membership)

    def memberships(self, project_id: str) -> tuple[ProjectMembershipDescriptor, ...]:
        """Return project-local membership descriptors."""
        return self._registry.memberships(project_id)

    def close(self) -> None:
        """Idempotently clear all local reference project state."""
        self._registry.clear()
