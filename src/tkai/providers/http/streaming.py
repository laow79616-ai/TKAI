"""Provider-neutral SSE, delta normalization, and retry boundaries."""

from __future__ import annotations

import json
from collections.abc import AsyncIterable, AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SSEEvent:
    """A completed Server-Sent Event."""

    data: str
    event: str | None = None
    id: str | None = None
    retry: int | None = None


@dataclass(frozen=True, slots=True)
class StreamDelta:
    """Normalized provider-independent response increment."""

    content: str = ""
    role: str | None = None
    tool_calls: tuple[dict[str, Any], ...] = ()
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    request_id: str | None = None


async def parse_sse(lines: AsyncIterable[bytes]) -> AsyncIterator[SSEEvent]:
    """Parse SSE fields, including multi-line data and terminal blank lines."""
    fields: dict[str, Any] = {}
    data: list[str] = []
    async for raw in lines:
        for line in raw.decode("utf-8").splitlines():
            if not line:
                if data:
                    yield SSEEvent("\n".join(data), **fields)
                fields, data = {}, []
                continue
            key, _, value = line.partition(":")
            value = value.lstrip(" ")
            if key == "data":
                data.append(value)
            elif key == "event":
                fields["event"] = value
            elif key == "id":
                fields["id"] = value
            elif key == "retry":
                try:
                    fields["retry"] = int(value)
                except ValueError:
                    pass
    if data:
        yield SSEEvent("\n".join(data), **fields)


async def parse_openai_deltas(
    events: AsyncIterable[SSEEvent],
) -> AsyncIterator[StreamDelta]:
    """Normalize compatible OpenAI-shaped JSON SSE events."""
    async for event in events:
        if event.data == "[DONE]":
            return
        try:
            payload = json.loads(event.data)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid streaming JSON") from exc
        choice = payload.get("choices", [{}])[0]
        delta = choice.get("delta", {})
        yield StreamDelta(
            delta.get("content") or "",
            delta.get("role"),
            tuple(delta.get("tool_calls", ())),
            choice.get("finish_reason"),
            payload.get("usage"),
            payload.get("id") or event.id,
        )


async def retry_stream(
    factory: Callable[[], AsyncIterable[StreamDelta]], *, retries: int = 0
) -> AsyncIterator[StreamDelta]:
    """Retry only failures raised before an output delta is yielded."""
    for attempt in range(retries + 1):
        emitted = False
        try:
            async for item in factory():
                emitted = True
                yield item
            return
        except Exception:
            if emitted or attempt == retries:
                raise
