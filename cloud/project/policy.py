"""Project validation policy contracts without access or lifecycle enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..models import Project
from .context import ProjectContext
from .models import WorkspaceProjectBinding


@dataclass(frozen=True, slots=True)
class ProjectValidation:
    """Declarative validation result with no side effects."""

    valid: bool
    warnings: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


class ProjectPolicy(Protocol):
    """Future caller-invoked policy boundary for project declarations."""

    def validate_creation(self, project: Project) -> ProjectValidation: ...
    def validate_update(self, project: Project) -> ProjectValidation: ...
    def validate_context(self, context: ProjectContext) -> ProjectValidation: ...
    def validate_binding(
        self, binding: WorkspaceProjectBinding
    ) -> ProjectValidation: ...
