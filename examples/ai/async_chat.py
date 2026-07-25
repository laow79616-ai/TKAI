"""Minimal asynchronous chat example without network access."""

from __future__ import annotations

import asyncio

from examples.ai.common import ExampleProvider
from tkai.ai import ChatMessage, ChatRequest, ProviderManager


async def arun() -> str:
    """Return a response through the asynchronous manager API."""
    manager = ProviderManager()
    manager.register(ExampleProvider(), default=True)
    response = await manager.achat(ChatRequest((ChatMessage("user", "hello"),)))
    return response.content


def run() -> str:
    """Run the standalone asynchronous example in a normal Python process."""
    return asyncio.run(arun())


if __name__ == "__main__":
    print(run())
