"""The sole Studio-to-SDK integration boundary."""

from __future__ import annotations

from tkai.sdk import Agent, AgentResponse
from tkai.sdk.workflow import ExecutionContext, WorkflowResult, WorkflowRuntime


class StudioIntegrationError(RuntimeError):
    """Raised when an explicitly injected SDK capability is unavailable."""


class SDKStudioGateway:
    """Delegate Studio operations to explicitly supplied public SDK objects only."""

    def __init__(
        self,
        *,
        agent: Agent | None = None,
        workflow_runtime: WorkflowRuntime | None = None,
    ) -> None:
        self._agent = agent
        self._workflow_runtime = workflow_runtime

    def chat(self, message: object, **options: object) -> AgentResponse:
        """Delegate chat through the public Agent SDK facade."""
        if self._agent is None:
            raise StudioIntegrationError("Studio chat requires an explicit SDK Agent.")
        return self._agent.chat(message, **options)

    def execute_workflow(
        self, context: ExecutionContext | None = None
    ) -> WorkflowResult:
        """Delegate execution through the public WorkflowRuntime SDK interface."""
        if self._workflow_runtime is None:
            raise StudioIntegrationError(
                "Studio execution requires an explicit SDK WorkflowRuntime."
            )
        return self._workflow_runtime.execute(context)
