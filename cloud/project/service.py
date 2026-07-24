"""Project service Protocols without transport, deployment, or persistence."""

from __future__ import annotations

from typing import Protocol

from ..models import Project
from .models import ProjectMembershipDescriptor


class ProjectService(Protocol):
    """Future explicit project service boundary for callers and adapters."""

    def project(self, project_id: str) -> Project: ...
    def projects(self, workspace_id: str | None = None) -> tuple[Project, ...]: ...
    def memberships(
        self, project_id: str
    ) -> tuple[ProjectMembershipDescriptor, ...]: ...
