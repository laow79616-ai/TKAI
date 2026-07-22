"""Minimal synchronous streaming example without network access."""

from __future__ import annotations

from examples.ai.common import ExampleProvider
from tkai.ai import ChatMessage, ChatRequest, ProviderManager


def run() -> list[str]:
    """Return all stream chunks in their stable emitted order."""
    manager = ProviderManager()
    manager.register(ExampleProvider(), default=True)
    request = ChatRequest((ChatMessage("user", "hello"),))
    return [item.content for item in manager.stream_chat(request)]


if __name__ == "__main__":
    print(run())
