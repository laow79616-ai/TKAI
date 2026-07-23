"""Project service validation and repository delegation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace

from studio.shared import StudioProject

from ..repositories.projects import InMemoryProjectRepository


class ProjectService:
    """Create and manage local project descriptors through an explicit repository."""

    def __init__(
        self,
        repository: InMemoryProjectRepository,
        *,
        id_factory: Callable[[str], str],
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory

    def create(
        self,
        name: str,
        *,
        description: str = "",
        metadata: Mapping[str, object] | None = None,
        project_id: str | None = None,
    ) -> StudioProject:
        """Create one local project with a caller- or factory-provided identifier."""
        return self._repository.create(
            StudioProject(
                project_id or self._id_factory("project"),
                name,
                description,
                metadata or {},
            )
        )

    def get(self, project_id: str) -> StudioProject:
        """Read one project snapshot."""
        return self._repository.get(project_id)

    def list(self) -> tuple[StudioProject, ...]:
        """List stable project snapshots."""
        return self._repository.list()

    def update(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> StudioProject:
        """Apply an explicit immutable project update."""
        current = self.get(project_id)
        return self._repository.update(
            replace(
                current,
                name=current.name if name is None else name,
                description=current.description if description is None else description,
                metadata=current.metadata if metadata is None else metadata,
            )
        )

    def delete(self, project_id: str) -> None:
        """Delete one project reference."""
        self._repository.delete(project_id)
