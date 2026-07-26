"""Workflow domain models and lifecycle values."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class NodeType(str, Enum):
    START = "start"
    END = "end"
    AGENT = "agent"
    TOOL = "tool"
    PLUGIN = "plugin"
    WORKFLOW = "workflow"
    CONDITION = "condition"
    SWITCH = "switch"
    LOOP = "loop"
    DELAY = "delay"
    APPROVAL = "approval"
    FORM = "form"
    WEBHOOK = "webhook"
    HTTP = "http"
    KNOWLEDGE = "knowledge"
    RAG = "rag"
    MODEL = "model"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class Scope:
    tenant: str
    workspace: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace:
            raise ValueError("Tenant and workspace are required.")


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    type: NodeType
    name: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    position: tuple[float, float] = (0, 0)
    group: str | None = None


@dataclass(frozen=True, slots=True)
class Edge:
    source: str
    target: str
    condition: str | None = None


@dataclass(frozen=True, slots=True)
class Workflow:
    id: str
    name: str
    description: str
    version: int
    owner: str
    tenant: str
    workspace: str
    status: WorkflowStatus = WorkflowStatus.DRAFT
    category: str = "general"
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    nodes: tuple[Node, ...] = ()
    edges: tuple[Edge, ...] = ()

    @property
    def scope(self) -> Scope:
        return Scope(self.tenant, self.workspace)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Execution:
    id: str
    workflow_id: str
    scope: Scope
    status: WorkflowStatus
    mode: str
    input: dict[str, Any]
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    attempts: int = 1
    checkpoint: int = 0
    duration_seconds: float = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
