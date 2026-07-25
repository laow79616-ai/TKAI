"""Offline streaming transport tests."""

import asyncio

from tkai.providers.http import (
    StreamDelta,
    parse_openai_deltas,
    parse_sse,
    retry_stream,
)


async def _lines():
    yield (
        b'event: message\ndata: {"id":"r","choices":[{"delta":{"role":"assistant",'
        b'"content":"he"}}]}\n\n'
    )
    yield (
        b'data: {"choices":[{"delta":{"content":"llo"},"finish_reason":"stop"}],'
        b'"usage":{"total_tokens":2}}\n\ndata: [DONE]\n\n'
    )


def test_sse_delta_done_and_usage() -> None:
    async def run():
        items = [item async for item in parse_openai_deltas(parse_sse(_lines()))]
        assert [item.content for item in items] == ["he", "llo"]
        assert items[-1].finish_reason == "stop" and items[-1].usage == {
            "total_tokens": 2
        }

    asyncio.run(run())


def test_retry_boundary_prevents_duplicate_output() -> None:
    async def run():
        calls = 0

        async def factory():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("before")
            yield StreamDelta("ok")

        assert [item.content async for item in retry_stream(factory, retries=1)] == [
            "ok"
        ]

    asyncio.run(run())
