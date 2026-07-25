"""Explicit SDK gateway execution service for offline Studio reference runs."""

from __future__ import annotations

from collections.abc import Callable

from studio.backend.errors import StudioExecutionError
from studio.shared import ExecutionRecord, ExecutionStatus
from tkai.sdk.workflow import ExecutionContext, WorkflowState

from ..gateway import SDKStudioGateway
from ..repositories.executions import InMemoryExecutionRepository
from ..repositories.workflows import InMemoryWorkflowRepository


class ExecutionService:
    """Create local records and delegate execution solely through SDKStudioGateway."""

    def __init__(
        self,
        repository: InMemoryExecutionRepository,
        workflow_repository: InMemoryWorkflowRepository,
        gateway: SDKStudioGateway,
        *,
        id_factory: Callable[[str], str],
    ) -> None:
        self._repository = repository
        self._workflow_repository = workflow_repository
        self._gateway = gateway
        self._id_factory = id_factory

    def execute(
        self, workflow_id: str, context: ExecutionContext | None = None
    ) -> ExecutionRecord:
        """Run an explicitly configured SDK workflow and record its mapped state."""
        workflow = self._workflow_repository.get(workflow_id)
        record = self._repository.create(
            ExecutionRecord(
                self._id_factory("execution"),
                workflow_id,
                ExecutionStatus.PENDING,
                project_id=workflow.project_id,
            )
        )
        try:
            result = self._gateway.execute_workflow(context)
        except Exception as error:
            self._repository.update_status(
                record.execution_id,
                ExecutionStatus.FAILED,
                error="SDK workflow execution failed.",
            )
            raise StudioExecutionError("Studio workflow execution failed.") from error
        return self._repository.update_status(
            record.execution_id,
            _execution_status(result.state),
            output=result.output,
            error=str(result.error) if result.error is not None else None,
        )

    def get(self, execution_id: str) -> ExecutionRecord:
        """Read one execution record."""
        return self._repository.get(execution_id)

    def list(
        self,
        *,
        project_id: str | None = None,
        workflow_id: str | None = None,
    ) -> tuple[ExecutionRecord, ...]:
        """List execution records using deterministic local repository filters."""
        return self._repository.list(project_id=project_id, workflow_id=workflow_id)


def _execution_status(state: WorkflowState) -> ExecutionStatus:
    """Map public SDK workflow states to Studio's API-visible state vocabulary."""
    return {
        WorkflowState.PENDING: ExecutionStatus.PENDING,
        WorkflowState.RUNNING: ExecutionStatus.RUNNING,
        WorkflowState.SUCCEEDED: ExecutionStatus.SUCCEEDED,
        WorkflowState.FAILED: ExecutionStatus.FAILED,
        WorkflowState.CANCELLED: ExecutionStatus.CANCELLED,
        WorkflowState.TIMED_OUT: ExecutionStatus.FAILED,
    }[state]
