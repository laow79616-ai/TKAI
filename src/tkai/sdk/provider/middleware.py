"""Composable synchronous middleware pipeline for explicit provider clients."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .request import ProviderRequest
from .response import ProviderResponse


class ProviderMiddleware(Protocol):
    """Middleware hook contract for request, response, and error boundaries."""

    def before_request(self, request: ProviderRequest) -> ProviderRequest: ...
    def after_response(self, response: ProviderResponse) -> ProviderResponse: ...
    def on_error(self, error: Exception) -> None: ...


class MiddlewarePipeline:
    """Apply ordered middleware around an explicit transport callable."""

    def __init__(self, middleware: tuple[ProviderMiddleware, ...] = ()) -> None:
        self.middleware = middleware

    def execute(
        self,
        request: ProviderRequest,
        transport: Callable[[ProviderRequest], ProviderResponse],
    ) -> ProviderResponse:
        """Run before/after/error hooks; errors continue to the original caller."""
        current = request
        try:
            for item in self.middleware:
                current = item.before_request(current)
            response = transport(current)
            for item in reversed(self.middleware):
                response = item.after_response(response)
            return response
        except Exception as error:
            for item in self.middleware:
                try:
                    item.on_error(error)
                except Exception:
                    continue
            raise
