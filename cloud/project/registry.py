"""Thread-safe in-memory Project registry for reference-only Cloud use."""

from __future__ import annotations

from threading import RLock

from ..models import Project
from .errors import ProjectConflictError, ProjectNotFoundError
from .models import ProjectMembershipDescriptor, WorkspaceProjectBinding


class ProjectRegistry:
    """Maintain local project and declarative relationship snapshots."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._projects: dict[str, Project] = {}
        self._bindings: dict[str, WorkspaceProjectBinding] = {}
        self._memberships: dict[tuple[str, str], ProjectMembershipDescriptor] = {}

    def register(self, project: Project) -> Project:
        """Register one immutable project or raise on an identifier conflict."""
        with self._lock:
            if project.project_id in self._projects:
                raise ProjectConflictError(project.project_id)
            self._projects[project.project_id] = project
            self._bindings[project.project_id] = WorkspaceProjectBinding(
                project.workspace_id, project.project_id
            )
            return project

    def unregister(self, project_id: str) -> Project:
        """Remove a project and its local declarative relationships."""
        with self._lock:
            try:
                project = self._projects.pop(project_id)
            except KeyError as exc:
                raise ProjectNotFoundError(project_id) from exc
            self._bindings.pop(project_id, None)
            self._memberships = {
                key: value
                for key, value in self._memberships.items()
                if value.project_id != project_id
            }
            return project

    def get(self, project_id: str) -> Project:
        """Return a registered immutable project snapshot."""
        with self._lock:
            try:
                return self._projects[project_id]
            except KeyError as exc:
                raise ProjectNotFoundError(project_id) from exc

    def exists(self, project_id: str) -> bool:
        """Return whether a project has been locally registered."""
        with self._lock:
            return project_id in self._projects

    def list(self, workspace_id: str | None = None) -> tuple[Project, ...]:
        """Return project snapshots in stable project-id order."""
        with self._lock:
            return tuple(
                project
                for _, project in sorted(self._projects.items())
                if workspace_id is None or project.workspace_id == workspace_id
            )

    def snapshot(self) -> tuple[Project, ...]:
        """Return a stable immutable snapshot of all projects."""
        return self.list()

    def binding(self, project_id: str) -> WorkspaceProjectBinding:
        """Return the declared workspace/project binding for a known project."""
        with self._lock:
            try:
                return self._bindings[project_id]
            except KeyError as exc:
                raise ProjectNotFoundError(project_id) from exc

    def hierarchy(self, workspace_id: str) -> tuple[WorkspaceProjectBinding, ...]:
        """Return stable bindings for one explicit workspace identifier."""
        with self._lock:
            return tuple(
                binding
                for _, binding in sorted(self._bindings.items())
                if binding.workspace_id == workspace_id
            )

    def add_membership(
        self, membership: ProjectMembershipDescriptor
    ) -> ProjectMembershipDescriptor:
        """Record a project-local membership without inheriting workspace access."""
        with self._lock:
            if membership.project_id not in self._projects:
                raise ProjectNotFoundError(membership.project_id)
            self._memberships[(membership.project_id, membership.principal_id)] = (
                membership
            )
            return membership

    def memberships(self, project_id: str) -> tuple[ProjectMembershipDescriptor, ...]:
        """Return local project membership descriptors in stable principal order."""
        with self._lock:
            if project_id not in self._projects:
                raise ProjectNotFoundError(project_id)
            return tuple(
                membership
                for _, membership in sorted(self._memberships.items())
                if membership.project_id == project_id
            )

    def clear(self) -> None:
        """Idempotently remove all in-memory project reference state."""
        with self._lock:
            self._projects.clear()
            self._bindings.clear()
            self._memberships.clear()
