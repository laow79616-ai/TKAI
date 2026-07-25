"""Bounded synchronous streaming contracts with async capability reserved."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from .response import ProviderResponse


@dataclass(frozen=True, slots=True)
class StreamChunk:
    """One immutable streaming chunk; ``finished`` marks terminal output."""

    response: ProviderResponse | None = None
    finished: bool = False


class StreamingResponse(Iterator[StreamChunk], Protocol):
    """Synchronous streaming contract with explicit cancellation and closing."""

    def cancel(self) -> None: ...
    def close(self) -> None: ...


class AsyncStreamingResponse(Protocol):
    """Reserved async-stream contract; no background task is created by the SDK."""

    def __aiter__(self) -> AsyncStreamingResponse: ...
    async def __anext__(self) -> StreamChunk: ...
    async def cancel(self) -> None: ...
    async def aclose(self) -> None: ...


class ReferenceStream:
    """Finite in-memory stream used for deterministic tests and examples."""

    def __init__(self, chunks: tuple[StreamChunk, ...]) -> None:
        self._chunks = chunks
        self._index = 0
        self.cancelled = False
        self.closed = False

    def __iter__(self) -> ReferenceStream:
        return self

    def __next__(self) -> StreamChunk:
        if self.closed or self._index >= len(self._chunks):
            raise StopIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk

    def cancel(self) -> None:
        """Stop further synchronous chunks without background cleanup work."""
        self.cancelled = True
        self.close()

    def close(self) -> None:
        """Close idempotently and release the finite local sequence."""
        self.closed = True
