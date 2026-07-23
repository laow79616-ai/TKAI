"""Service composition tests use an injected public SDK workflow runtime."""

from __future__ import annotations

import pytest

from studio.backend import SDKStudioGateway, StudioDependencies
from studio.backend.errors import StudioExecutionError, StudioNotFoundError
from studio.shared import ExecutionStatus, StudioWorkflow
from tkai.sdk.workflow import Node, WorkflowBuilder, WorkflowRuntime


def _dependencies() -> StudioDependencies:
    definition = WorkflowBuilder("local").add(Node("task", handler="done")).build()
    return StudioDependencies.create(
        sdk_gateway=SDKStudioGateway(workflow_runtime=WorkflowRuntime(definition))
    )


def test_services_validate_project_workflow_and_gateway_execution() -> None:
    """Execution passes through SDKStudioGateway and records the mapped result."""
    dependencies = _dependencies()
    project = dependencies.project_service.create("Project", project_id="project")
    workflow = dependencies.workflow_service.create(
        StudioWorkflow("workflow", project.project_id, "Workflow")
    )
    execution = dependencies.execution_service.execute(workflow.workflow_id)

    assert execution.status is ExecutionStatus.SUCCEEDED
    assert execution.output == "done"
    with pytest.raises(StudioNotFoundError):
        dependencies.workflow_service.create(
            StudioWorkflow("other", "missing", "Other")
        )


def test_gateway_failure_is_mapped_without_swallowing_the_cause() -> None:
    """SDK failures become StudioExecutionError and retain the exception chain."""
    dependencies = StudioDependencies.create(sdk_gateway=SDKStudioGateway())
    project = dependencies.project_service.create("Project", project_id="project")
    workflow = dependencies.workflow_service.create(
        StudioWorkflow("workflow", project.project_id, "Workflow")
    )

    with pytest.raises(StudioExecutionError) as raised:
        dependencies.execution_service.execute(workflow.workflow_id)
    assert raised.value.__cause__ is not None
