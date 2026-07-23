"""Optional observation interfaces for explicit Tool SDK execution."""

from __future__ import annotations

from typing import Protocol

from .context import ToolRequest
from .result import ToolResult


class ToolHook(Protocol):
    """Observe execution without taking ownership of a tool or its context."""

    def before_execute(self, request: ToolRequest) -> None: ...

    def after_execute(self, request: ToolRequest, result: ToolResult) -> None: ...

    def on_error(self, request: ToolRequest, error: Exception) -> None: ...


class TelemetryToolHook(ToolHook, Protocol):
    """Marker protocol for an explicitly injected telemetry observer."""
