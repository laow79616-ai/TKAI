"""Unified provider-client protocol and deterministic reference implementation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from .capability import ProviderCapability
from .configuration import ProviderConfiguration
from .errors import ProviderLifecycleError
from .lifecycle import ProviderLifecycle
from .request import ProviderRequest
from .response import ProviderResponse
from .streaming import ReferenceStream, StreamChunk, StreamingResponse


class ProviderClient(Protocol):
    """Provider SDK client contract for explicitly constructed implementations."""

    @property
    def name(self) -> str: ...
    @property
    def capabilities(self) -> frozenset[ProviderCapability]: ...
    @property
    def lifecycle(self) -> ProviderLifecycle: ...
    def execute(self, request: ProviderRequest) -> ProviderResponse: ...
    def stream(self, request: ProviderRequest) -> StreamingResponse: ...
    def close(self) -> None: ...


@dataclass(slots=True)
class ReferenceProvider:
    """Offline-only deterministic ProviderClient for tests, docs, and SDK smoke."""

    provider_name: str = "reference"
    configuration: ProviderConfiguration = ProviderConfiguration()
    responder: Callable[[ProviderRequest], object] | None = None
    _closed: bool = field(default=False, init=False, repr=False)

    @property
    def name(self) -> str:
        """Return the stable local provider name."""
        return self.provider_name

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        """Expose local chat, streaming, function, and JSON-mode capabilities."""
        return frozenset(
            {
                ProviderCapability.CHAT,
                ProviderCapability.STREAMING,
                ProviderCapability.FUNCTION_CALLING,
                ProviderCapability.JSON_MODE,
            }
        )

    @property
    def lifecycle(self) -> ProviderLifecycle:
        """Return the observable lifecycle of the local reference client."""
        return ProviderLifecycle.CLOSED if self._closed else ProviderLifecycle.ACTIVE

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        """Return deterministic local output from the optional responder."""
        if self._closed:
            raise ProviderLifecycleError("Reference provider is closed.")
        output = self.responder(request) if self.responder else request.input
        return ProviderResponse(
            output, self.name, request.model or self.configuration.model
        )

    def stream(self, request: ProviderRequest) -> StreamingResponse:
        """Return a finite local response followed by an explicit finish chunk."""
        if self._closed:
            raise ProviderLifecycleError("Reference provider is closed.")
        return ReferenceStream(
            (StreamChunk(self.execute(request)), StreamChunk(finished=True))
        )

    def close(self) -> None:
        """Close the local provider; repeated closes are safe."""
        self._closed = True
