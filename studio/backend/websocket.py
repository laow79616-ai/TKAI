"""WebSocket interface definitions without a socket server implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class StudioWebSocket(Protocol):
    """Minimal asynchronous socket interface used for execution event delivery."""

    async def accept(self) -> None: ...
    async def send_json(self, payload: Mapping[str, object]) -> None: ...
    async def close(self) -> None: ...
