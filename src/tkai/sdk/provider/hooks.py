"""Optional hook contracts for retry, telemetry, logging, and metrics adapters."""

from __future__ import annotations

from typing import Protocol

from .request import ProviderRequest
from .response import ProviderResponse


class ProviderHook(Protocol):
    """Observer contract; implementations are explicitly supplied by applications."""

    def before_request(self, request: ProviderRequest) -> None: ...
    def after_response(self, response: ProviderResponse) -> None: ...
    def on_error(self, error: Exception) -> None: ...


class RetryHook(ProviderHook, Protocol):
    """Marker protocol for explicit retry-aware middleware hooks."""


class TelemetryHook(ProviderHook, Protocol):
    """Marker protocol for explicit telemetry middleware hooks."""


class LoggingHook(ProviderHook, Protocol):
    """Marker protocol for explicit structured-logging middleware hooks."""


class MetricsHook(ProviderHook, Protocol):
    """Marker protocol for explicit metrics middleware hooks."""
