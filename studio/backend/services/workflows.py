"""Workflow-service validation for visual Studio declarations."""

from __future__ import annotations

from dataclasses import replace

from studio.backend.errors import StudioValidationError
from studio.shared import StudioWorkflow

from ..repositories.projects import InMemoryProjectRepository
from ..repositories.workflows import InMemoryWorkflowRepository


class WorkflowService:
    """Manage visual workflows while checking their referenced project exists."""

    def __init__(
        self,
        repository: InMemoryWorkflowRepository,
        project_repository: InMemoryProjectRepository,
    ) -> None:
        self._repository = repository
        self._project_repository = project_repository

    def create(self, workflow: StudioWorkflow) -> StudioWorkflow:
        """Store a structurally validated visual workflow for an existing project."""
        self._project_repository.get(workflow.project_id)
        self._validate(workflow)
        return self._repository.create(workflow)

    def get(self, workflow_id: str) -> StudioWorkflow:
        """Read a workflow snapshot."""
        return self._repository.get(workflow_id)

    def list(self, *, project_id: str | None = None) -> tuple[StudioWorkflow, ...]:
        """List workflows with an optional project filter."""
        return self._repository.list(project_id=project_id)

    def update(self, workflow_id: str, workflow: StudioWorkflow) -> StudioWorkflow:
        """Replace a workflow only when its URI id agrees with the payload."""
        if workflow.workflow_id != workflow_id:
            raise StudioValidationError(
                "Workflow id must match the requested resource."
            )
        self._project_repository.get(workflow.project_id)
        self._validate(workflow)
        return self._repository.update(workflow)

    def patch_name(self, workflow_id: str, name: str) -> StudioWorkflow:
        """Provide a small immutable patch path for API smoke coverage."""
        if not name:
            raise StudioValidationError("Workflow name must not be empty.")
        return self._repository.update(replace(self.get(workflow_id), name=name))

    def delete(self, workflow_id: str) -> None:
        """Delete a visual workflow declaration."""
        self._repository.delete(workflow_id)

    @staticmethod
    def _validate(workflow: StudioWorkflow) -> None:
        if not workflow.nodes:
            return
        if any(not node.label for node in workflow.nodes):
            raise StudioValidationError("Workflow nodes must have labels.")
