"""Visual agent/tool workflow graphs with conditions, retry, and checkpoints."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum

from studio.metrics import StudioMetrics


class NodeType(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    RETRY = "retry"
    CHECKPOINT = "checkpoint"


@dataclass(frozen=True, slots=True)
class WorkflowNode:
    node_id: str
    node_type: NodeType
    configuration: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowEdge:
    source: str
    target: str
    condition: str | None = None


@dataclass(frozen=True, slots=True)
class VisualWorkflow:
    workflow_id: str
    project_id: str
    name: str
    nodes: tuple[WorkflowNode, ...]
    edges: tuple[WorkflowEdge, ...]

    def validate(self) -> None:
        ids = {node.node_id for node in self.nodes}
        if len(ids) != len(self.nodes):
            raise ValueError("Workflow node ids must be unique.")
        if any(edge.source not in ids or edge.target not in ids for edge in self.edges):
            raise ValueError("Workflow edges must reference declared nodes.")


@dataclass(frozen=True, slots=True)
class WorkflowRun:
    run_id: str
    workflow_id: str
    status: str
    checkpoints: tuple[str, ...] = ()


class WorkflowStudio:
    """Store visual graphs and delegate execution to the preserved runtime."""

    def __init__(
        self,
        id_factory: Callable[[str], str],
        execute: Callable[[VisualWorkflow], tuple[str, ...]],
        metrics: StudioMetrics | None = None,
    ) -> None:
        self._id_factory = id_factory
        self._execute = execute
        self._metrics = metrics or StudioMetrics()
        self._items: dict[str, VisualWorkflow] = {}

    def save(self, workflow: VisualWorkflow) -> VisualWorkflow:
        workflow.validate()
        self._items[workflow.workflow_id] = workflow
        return workflow

    def run(self, workflow_id: str) -> WorkflowRun:
        workflow = self._items[workflow_id]
        checkpoints = self._execute(workflow)
        run = WorkflowRun(
            self._id_factory("workflow-run"),
            workflow_id,
            "succeeded",
            checkpoints,
        )
        self._metrics.increment("workflow_runs")
        return run


__all__ = (
    "NodeType",
    "VisualWorkflow",
    "WorkflowEdge",
    "WorkflowNode",
    "WorkflowRun",
    "WorkflowStudio",
)
