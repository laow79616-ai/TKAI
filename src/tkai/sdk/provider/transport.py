"""Provider transport protocols without any network implementation."""

from __future__ import annotations

from typing import Protocol

from .request import ProviderRequest
from .response import ProviderResponse
from .streaming import StreamingResponse


class ProviderTransport(Protocol):
    """Transport contract implemented by future explicit vendor adapters."""

    def send(self, request: ProviderRequest) -> ProviderResponse: ...
    def stream(self, request: ProviderRequest) -> StreamingResponse: ...
    def close(self) -> None: ...
