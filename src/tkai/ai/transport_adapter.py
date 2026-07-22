"""Compatibility adapter from legacy callable transports to AsyncTransport."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any

from .runtime import AsyncTransport

LegacyTransport = Callable[[str, dict[str, Any], dict[str, str]], Any]


class TransportAdapter(AsyncTransport):
    """Wrap a legacy callable without making providers depend on its shape."""

    def __init__(self, callback: LegacyTransport) -> None:
        self._callback = callback
        self._closed = False

    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        if self._closed:
            raise RuntimeError("transport is closed")
        return await asyncio.to_thread(
            self._callback, url, kwargs.get("json", {}), kwargs.get("headers", {})
        )

    async def stream(
        self, method: str, url: str, **kwargs: Any
    ) -> AsyncIterator[bytes]:
        result = await self.request(method, url, **kwargs)
        for item in result if not isinstance(result, dict) else (result,):
            yield str(item).encode()

    async def close(self) -> None:
        self._closed = True

    def health_check(self) -> bool:
        return not self._closed
