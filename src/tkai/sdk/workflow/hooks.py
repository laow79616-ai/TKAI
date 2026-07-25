"""Non-owning hook protocols for explicit reference workflow observation."""

from __future__ import annotations

from typing import Protocol

from .definitions import Node


class WorkflowHook(Protocol):
    """Observe workflow execution without controlling runtime ownership."""

    def before_execute(self) -> None: ...

    def after_execute(self) -> None: ...

    def before_node(self, node: Node) -> None: ...

    def after_node(self, node: Node) -> None: ...

    def on_error(self, node: Node | None, error: Exception) -> None: ...


class TelemetryWorkflowHook(WorkflowHook, Protocol):
    """Marker protocol for an explicitly injected telemetry observer."""
