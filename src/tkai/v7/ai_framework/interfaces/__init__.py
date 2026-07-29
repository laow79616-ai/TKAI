"""Non-executable inference interfaces."""

from typing import Protocol

from ..contracts import RouteDecision, RouteRequest


class ModelRouter(Protocol):
    """Metadata-only routing interface."""

    def route(self, request: RouteRequest) -> RouteDecision: ...


__all__ = ("ModelRouter",)
