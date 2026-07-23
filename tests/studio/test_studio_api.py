"""Studio service tests use explicitly injected SDK objects only."""

from __future__ import annotations

import pytest

from studio.backend import SDKStudioGateway, StudioIntegrationError, StudioService
from studio.shared import ExecutionStatus, StudioProject, StudioWorkflow
from tkai.sdk import Agent
from tkai.sdk.adapters import InMemoryProvider, ProviderAdapter, V1RuntimeAdapter
from tkai.sdk.workflow import ExecutionContext, Node, WorkflowBuilder, WorkflowRuntime


def test_studio_gateway_uses_explicit_sdk_agent_and_workflow_runtime() -> None:
    """The Studio reference service has no direct V1.x Runtime dependency."""
    definition = WorkflowBuilder("local").add(Node("task", handler="done")).build()
    runtime = WorkflowRuntime(definition)
    agent = Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider())))
    gateway = SDKStudioGateway(agent=agent, workflow_runtime=runtime)
    service = StudioService(gateway)
    project = service.create_project(StudioProject("project", "Project"))
    workflow = service.save_workflow(
        StudioWorkflow("workflow", project.project_id, "Flow")
    )

    assert gateway.chat("hello").output == "hello"
    execution = service.execute(workflow.workflow_id, ExecutionContext())

    assert execution.status is ExecutionStatus.SUCCEEDED
    assert execution.output == "done"
    assert service.list_projects() == (project,)


def test_studio_gateway_requires_explicit_sdk_dependencies() -> None:
    """Studio never constructs an Agent or workflow runtime as a hidden default."""
    gateway = SDKStudioGateway()

    with pytest.raises(StudioIntegrationError, match="explicit SDK Agent"):
        gateway.chat("hello")
    with pytest.raises(StudioIntegrationError, match="explicit SDK WorkflowRuntime"):
        gateway.execute_workflow()
