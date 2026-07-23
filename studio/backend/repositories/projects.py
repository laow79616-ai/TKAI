"""Thread-safe reference project repository with no persistence or I/O."""

from __future__ import annotations

from threading import RLock

from studio.backend.errors import StudioConflictError, StudioNotFoundError
from studio.shared import StudioProject


class InMemoryProjectRepository:
    """Store immutable project snapshots in local process memory only."""

    def __init__(self) -> None:
        self._items: dict[str, StudioProject] = {}
        self._lock = RLock()

    def create(self, project: StudioProject) -> StudioProject:
        """Create a project, rejecting duplicate identifiers deterministically."""
        with self._lock:
            if project.project_id in self._items:
                raise StudioConflictError(
                    f"Project already exists: {project.project_id}"
                )
            self._items[project.project_id] = project
            return project

    def get(self, project_id: str) -> StudioProject:
        """Return one immutable project or raise the stable not-found error."""
        with self._lock:
            try:
                return self._items[project_id]
            except KeyError as error:
                raise StudioNotFoundError(f"Project not found: {project_id}") from error

    def list(self) -> tuple[StudioProject, ...]:
        """Return projects in stable identifier order."""
        with self._lock:
            return tuple(self._items[key] for key in sorted(self._items))

    def update(self, project: StudioProject) -> StudioProject:
        """Replace a project snapshot when its identifier already exists."""
        with self._lock:
            if project.project_id not in self._items:
                raise StudioNotFoundError(f"Project not found: {project.project_id}")
            self._items[project.project_id] = project
            return project

    def delete(self, project_id: str) -> None:
        """Delete one local project reference without touching dependent resources."""
        with self._lock:
            if project_id not in self._items:
                raise StudioNotFoundError(f"Project not found: {project_id}")
            del self._items[project_id]

    def ready(self) -> bool:
        """Report local repository readiness without a network health check."""
        return True
