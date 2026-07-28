"""Enterprise workflow platform facade."""

from dataclasses import replace
from typing import Any

from .designer import Designer
from .engine import ExecutionEngine
from .execution import ExecutionOptions
from .history import History
from .metrics import WorkflowMetrics
from .models import Edge, Execution, Node, NodeType, Scope, Workflow, WorkflowStatus
from .templates import TemplateCatalog

TRANSITIONS = {
    WorkflowStatus.DRAFT: {WorkflowStatus.PUBLISHED, WorkflowStatus.DELETED},
    WorkflowStatus.PUBLISHED: {
        WorkflowStatus.RUNNING,
        WorkflowStatus.ARCHIVED,
        WorkflowStatus.DRAFT,
    },
    WorkflowStatus.RUNNING: {
        WorkflowStatus.PAUSED,
        WorkflowStatus.COMPLETED,
        WorkflowStatus.FAILED,
    },
    WorkflowStatus.PAUSED: {
        WorkflowStatus.RUNNING,
        WorkflowStatus.ARCHIVED,
    },
    WorkflowStatus.COMPLETED: {
        WorkflowStatus.RUNNING,
        WorkflowStatus.ARCHIVED,
    },
    WorkflowStatus.FAILED: {
        WorkflowStatus.RUNNING,
        WorkflowStatus.ARCHIVED,
    },
    WorkflowStatus.ARCHIVED: {WorkflowStatus.DRAFT, WorkflowStatus.DELETED},
    WorkflowStatus.DELETED: set(),
}


def workflow_from_payload(payload: dict[str, Any]) -> Workflow:
    nodes = tuple(
        Node(
            str(item["id"]),
            NodeType(str(item["type"])),
            str(item.get("name", "")),
            dict(item.get("config", {})),
        )
        for item in payload.get("nodes", ())
    )
    edges = tuple(
        Edge(str(item["source"]), str(item["target"]), item.get("condition"))
        for item in payload.get("edges", ())
    )
    return Workflow(
        id=str(payload["id"]),
        name=str(payload["name"]),
        description=str(payload.get("description", "")),
        version=int(payload.get("version", 1)),
        owner=str(payload["owner"]),
        tenant=str(payload["tenant"]),
        workspace=str(payload["workspace"]),
        status=WorkflowStatus(str(payload.get("status", "draft"))),
        category=str(payload.get("category", "general")),
        tags=tuple(str(tag) for tag in payload.get("tags", ())),
        metadata=dict(payload.get("metadata", {})),
        nodes=nodes,
        edges=edges,
    )


class WorkflowPlatform:
    def __init__(self, execution_limit: int = 100) -> None:
        self.workflows: dict[str, Workflow] = {}
        self.history = History()
        self.metrics = WorkflowMetrics()
        self.engine = ExecutionEngine(self.history, self.metrics)
        self.templates = TemplateCatalog()
        self.execution_limit = execution_limit

    def create(self, payload: dict[str, Any]) -> Workflow:
        item = workflow_from_payload(payload)
        if item.id in self.workflows:
            raise ValueError("Workflow already exists.")
        self.workflows[item.id] = item
        self.metrics.increment("workflow_total")
        return item

    def get(self, workflow_id: str, scope: Scope) -> Workflow:
        item = self.workflows[workflow_id]
        if item.scope != scope:
            raise PermissionError("Tenant or workspace isolation violation.")
        return item

    def list(self, scope: Scope) -> tuple[Workflow, ...]:
        return tuple(item for item in self.workflows.values() if item.scope == scope)

    def transition(
        self, workflow_id: str, scope: Scope, status: str
    ) -> Workflow:
        item = self.get(workflow_id, scope)
        target = WorkflowStatus(status)
        if target not in TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid transition: {item.status.value} -> {target.value}"
            )
        updated = replace(item, status=target)
        self.workflows[item.id] = updated
        return updated

    def publish(self, workflow_id: str, scope: Scope) -> Workflow:
        item = self.get(workflow_id, scope)
        errors = Designer(item).validate()
        if errors:
            raise ValueError(" ".join(errors))
        return self.transition(workflow_id, scope, "published")

    def run(
        self,
        workflow_id: str,
        scope: Scope,
        inputs: dict[str, Any],
        options: ExecutionOptions | None = None,
    ) -> Execution:
        if len(self.history.list(scope)) >= self.execution_limit:
            raise ValueError("Execution limit exceeded.")
        item = self.get(workflow_id, scope)
        if item.status not in {
            WorkflowStatus.PUBLISHED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
        }:
            raise ValueError("Workflow is not published.")
        return self.engine.run(item, inputs, options)
