"""In-memory architecture reference services for Studio REST route contracts."""

from __future__ import annotations

from threading import RLock

from studio.shared.models import (
    ExecutionRecord,
    ExecutionStatus,
    StudioProject,
    StudioWorkflow,
)
from tkai.sdk.workflow import ExecutionContext, WorkflowState

from ..gateway import SDKStudioGateway


class StudioService:
    """Small local store that demonstrates routing without owning the V1.x Runtime."""

    def __init__(self, gateway: SDKStudioGateway) -> None:
        self._gateway = gateway
        self._projects: dict[str, StudioProject] = {}
        self._workflows: dict[str, StudioWorkflow] = {}
        self._lock = RLock()

    def create_project(self, project: StudioProject) -> StudioProject:
        """Store an immutable project descriptor for the architecture reference."""
        with self._lock:
            if project.project_id in self._projects:
                raise ValueError(f"Studio project already exists: {project.project_id}")
            self._projects[project.project_id] = project
            return project

    def list_projects(self) -> tuple[StudioProject, ...]:
        """Return project descriptors in stable identifier order."""
        with self._lock:
            return tuple(self._projects[key] for key in sorted(self._projects))

    def save_workflow(self, workflow: StudioWorkflow) -> StudioWorkflow:
        """Store a designer declaration without compiling or executing it."""
        with self._lock:
            if workflow.project_id not in self._projects:
                raise ValueError(f"Unknown Studio project: {workflow.project_id}")
            self._workflows[workflow.workflow_id] = workflow
            return workflow

    def get_workflow(self, workflow_id: str) -> StudioWorkflow | None:
        """Return an immutable visual workflow declaration when it is registered."""
        with self._lock:
            return self._workflows.get(workflow_id)

    def execute(
        self, workflow_id: str, context: ExecutionContext | None = None
    ) -> ExecutionRecord:
        """Use the injected public SDK runtime and map its result to a Studio record."""
        if self.get_workflow(workflow_id) is None:
            raise ValueError(f"Unknown Studio workflow: {workflow_id}")
        result = self._gateway.execute_workflow(context)
        status = {
            WorkflowState.PENDING: ExecutionStatus.PENDING,
            WorkflowState.RUNNING: ExecutionStatus.RUNNING,
            WorkflowState.SUCCEEDED: ExecutionStatus.SUCCEEDED,
            WorkflowState.FAILED: ExecutionStatus.FAILED,
            WorkflowState.CANCELLED: ExecutionStatus.CANCELLED,
            WorkflowState.TIMED_OUT: ExecutionStatus.FAILED,
        }[result.state]
        return ExecutionRecord(
            execution_id=f"local-{workflow_id}",
            workflow_id=workflow_id,
            status=status,
            output=result.output,
            error=str(result.error) if result.error is not None else None,
        )
