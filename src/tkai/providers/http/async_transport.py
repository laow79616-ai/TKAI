"""Owned or injected ``httpx.AsyncClient`` transport."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class TransportResponse:
    """Safe normalized HTTP response metadata."""

    status_code: int
    data: Any
    headers: dict[str, str]
    request_id: str | None
    retry_after: str | None


class AsyncHTTPTransport:
    """Async HTTP client wrapper with explicit client ownership."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._owned = client is None
        self._closed = False
        self._client = client or httpx.AsyncClient(transport=transport, timeout=timeout)

    async def __aenter__(self) -> AsyncHTTPTransport:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def request(
        self,
        method: str,
        url: str,
        *,
        json: Any = None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> TransportResponse:
        """Send one JSON request through the configured connection pool."""
        if self._closed:
            raise RuntimeError("HTTP transport is closed")
        response = await self._client.request(
            method, url, json=json, headers=headers, params=params
        )
        try:
            data = response.json()
        except ValueError:
            data = response.text[:65536]
        return TransportResponse(
            response.status_code,
            data,
            dict(response.headers),
            response.headers.get("x-request-id"),
            response.headers.get("retry-after"),
        )

    async def get(self, url: str, **kwargs: Any) -> TransportResponse:
        """Issue a GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> TransportResponse:
        """Issue a POST request."""
        return await self.request("POST", url, **kwargs)

    async def stream(
        self, method: str, url: str, **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """Yield raw response bytes while ensuring response cleanup."""
        if self._closed:
            raise RuntimeError("HTTP transport is closed")
        async with self._client.stream(method, url, **kwargs) as response:
            async for chunk in response.aiter_bytes():
                yield chunk

    async def close(self) -> None:
        """Close only a client created by this transport, exactly once."""
        if not self._closed and self._owned:
            await self._client.aclose()
        self._closed = True
