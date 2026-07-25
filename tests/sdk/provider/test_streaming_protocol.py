"""Compatibility coverage for the SDK's asynchronous streaming contract."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from tkai.sdk.provider import AsyncStreamingResponse, StreamChunk


class _AsyncStream:
    def __init__(self, chunks: tuple[StreamChunk, ...]) -> None:
        self._chunks = iter(chunks)
        self.cancelled = False
        self.closed = False

    def __aiter__(self) -> _AsyncStream:
        return self

    async def __anext__(self) -> StreamChunk:
        try:
            return next(self._chunks)
        except StopIteration:
            raise StopAsyncIteration from None

    async def cancel(self) -> None:
        self.cancelled = True

    async def aclose(self) -> None:
        self.closed = True


def _accepts_async_stream(stream: AsyncStreamingResponse) -> AsyncIterator[StreamChunk]:
    return stream


def test_async_streaming_response_preserves_async_iterator_contract() -> None:
    """The SDK module imports and accepts a structural async iterator."""
    chunks = (StreamChunk(), StreamChunk(finished=True))
    stream = _AsyncStream(chunks)

    async def consume() -> list[StreamChunk]:
        contract = _accepts_async_stream(stream)
        received = [chunk async for chunk in contract]
        await stream.cancel()
        await stream.aclose()
        return received

    assert asyncio.run(consume()) == list(chunks)
    assert stream.cancelled is True
    assert stream.closed is True
