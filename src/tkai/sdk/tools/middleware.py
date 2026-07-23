"""Composable local middleware pipeline with failure-isolated observation hooks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .context import ToolRequest
from .result import ToolResult


class ToolMiddleware(Protocol):
    """Transform request/results around an explicit synchronous tool call."""

    def before_execute(self, request: ToolRequest) -> ToolRequest: ...

    def after_execute(self, result: ToolResult) -> ToolResult: ...

    def on_error(self, error: Exception) -> None: ...


class ToolMiddlewarePipeline:
    """Apply middleware in stable order without swallowing the primary exception."""

    def __init__(self, middleware: tuple[ToolMiddleware, ...] = ()) -> None:
        self.middleware = middleware

    def execute(self, tool: Tool, request: ToolRequest) -> ToolResult:
        """Invoke an explicit tool through its ordered local middleware chain."""
        current = request
        try:
            for item in self.middleware:
                current = item.before_execute(current)
            result = tool.execute(current)
            for item in reversed(self.middleware):
                result = item.after_execute(result)
            return result
        except Exception as error:
            for item in self.middleware:
                try:
                    item.on_error(error)
                except Exception:
                    continue
            raise


if TYPE_CHECKING:
    from .tool import Tool
