"""Immutable Studio view models; these do not execute a workflow directly."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType


class StudioNodeKind(str, Enum):
    """Visual workflow node categories presented by the Studio designer."""

    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    BRANCH = "branch"
    MEMORY = "memory"
    PROVIDER = "provider"
    END = "end"


class ExecutionStatus(str, Enum):
    """Read-only execution status exposed by Studio APIs."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class StudioProject:
    """A project descriptor with no implicit filesystem or runtime ownership."""

    project_id: str
    name: str
    description: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.project_id or not self.name:
            raise ValueError("Studio project id and name must not be empty.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class StudioNode:
    """A visual node definition, separate from SDK workflow execution nodes."""

    node_id: str
    kind: StudioNodeKind
    label: str
    position: tuple[int, int] = (0, 0)
    configuration: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id or not self.label:
            raise ValueError("Studio node id and label must not be empty.")
        object.__setattr__(
            self, "configuration", MappingProxyType(dict(self.configuration))
        )


@dataclass(frozen=True, slots=True)
class StudioWorkflow:
    """Immutable designer graph that can later be compiled to an SDK workflow."""

    workflow_id: str
    project_id: str
    name: str
    nodes: tuple[StudioNode, ...] = ()
    edges: tuple[tuple[str, str], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        node_ids = {node.node_id for node in self.nodes}
        if not self.workflow_id or not self.project_id or not self.name:
            raise ValueError("Studio workflow id, project id, and name are required.")
        if len(node_ids) != len(self.nodes):
            raise ValueError("Studio workflow node ids must be unique.")
        if any(
            source not in node_ids or target not in node_ids
            for source, target in self.edges
        ):
            raise ValueError("Studio workflow edges must refer to declared nodes.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    """Immutable execution summary emitted by the Studio execution boundary."""

    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    output: object | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.execution_id or not self.workflow_id:
            raise ValueError("Studio execution id and workflow id are required.")
