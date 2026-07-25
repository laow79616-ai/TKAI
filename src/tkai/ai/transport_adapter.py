"""Compatibility adapter from legacy callable transports to AsyncTransport."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Any, cast

from tkai.providers.http import AsyncHTTPTransport

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
            if isinstance(item, bytes):
                yield item
            elif isinstance(item, str):
                yield item.encode("utf-8")
            elif isinstance(item, (dict, list)):
                yield json.dumps(
                    item, ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")
            else:
                raise TypeError(
                    f"Unsupported legacy stream chunk: {type(item).__name__}"
                )

    async def close(self) -> None:
        self._closed = True

    def health_check(self) -> bool:
        return not self._closed


def resolve_transport(
    transport: AsyncTransport | LegacyTransport | None, *, timeout: float
) -> tuple[AsyncTransport, bool]:
    """Return a uniform async transport and whether the caller owns it."""
    if transport is None:
        return cast(AsyncTransport, AsyncHTTPTransport(timeout=timeout)), True
    if isinstance(transport, TransportAdapter) or hasattr(transport, "request"):
        return transport, False  # type: ignore[return-value]
    return TransportAdapter(transport), True
