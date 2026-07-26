"""Deterministic bounded workflow execution engine."""

from __future__ import annotations

from dataclasses import replace
from time import monotonic
from typing import Any
from uuid import uuid4

from workflow_platform.conditions import evaluate
from workflow_platform.execution import ExecutionOptions
from workflow_platform.history import History
from workflow_platform.metrics import WorkflowMetrics
from workflow_platform.models import Execution, Node, NodeType, Workflow, WorkflowStatus
from workflow_platform.variables import Variables


class ExecutionEngine:
    def __init__(self, history: History, metrics: WorkflowMetrics) -> None:
        self.history = history
        self.metrics = metrics
        self.handlers: dict[NodeType, Any] = {}
        self.cancelled: set[str] = set()

    def register(self, node_type: NodeType, handler: Any) -> None:
        self.handlers[node_type] = handler

    def run(
        self,
        workflow: Workflow,
        inputs: dict[str, Any],
        options: ExecutionOptions | None = None,
        *,
        execution_id: str | None = None,
        resume_from: int = 0,
    ) -> Execution:
        selected = options or ExecutionOptions()
        run_id = execution_id or str(uuid4())
        execution = Execution(
            run_id,
            workflow.id,
            workflow.scope,
            WorkflowStatus.RUNNING,
            selected.mode,
            inputs,
            checkpoint=resume_from,
        )
        self.history.save(execution)
        self.metrics.increment("workflow_runs_total")
        started = monotonic()
        variables = Variables(inputs=inputs)
        attempts = 0
        try:
            for index, node in enumerate(workflow.nodes[resume_from:], resume_from):
                if run_id in self.cancelled:
                    raise RuntimeError("Execution cancelled.")
                if monotonic() - started > selected.timeout_seconds:
                    raise TimeoutError("Execution timed out.")
                attempts = self._execute_with_retry(node, variables, selected.retries)
                if selected.checkpoint:
                    execution = replace(execution, checkpoint=index + 1)
                    self.history.save(execution)
            duration = monotonic() - started
            execution = replace(
                execution,
                status=WorkflowStatus.COMPLETED,
                output=variables.output(),
                attempts=max(1, attempts),
                duration_seconds=duration,
            )
            self.metrics.increment("workflow_success_total")
            self.metrics.increment("workflow_duration_seconds", duration)
        except Exception as exc:
            execution = replace(
                execution,
                status=WorkflowStatus.FAILED,
                error=str(exc),
                attempts=max(1, attempts),
                duration_seconds=monotonic() - started,
            )
            self.metrics.increment("workflow_failed_total")
        return self.history.save(execution)

    def _execute_with_retry(
        self, node: Node, variables: Variables, retries: int
    ) -> int:
        for attempt in range(1, retries + 2):
            try:
                if node.type is NodeType.CONDITION:
                    variables.values["runtime"][node.id] = evaluate(
                        node.config["operator"],
                        variables.resolve(node.config["left"]),
                        node.config.get("right"),
                    )
                elif node.type in self.handlers:
                    result = self.handlers[node.type](node, variables)
                    variables.values["runtime"][node.id] = result
                return attempt
            except Exception:
                if attempt > retries:
                    raise
        return retries + 1

    def cancel(self, execution_id: str) -> None:
        self.cancelled.add(execution_id)

    def rollback(self, execution_id: str, checkpoint: int) -> Execution:
        item = self.history._items[execution_id]
        return self.history.save(replace(item, checkpoint=checkpoint))
