"""Minimal synchronous chat example without network access."""

from __future__ import annotations

from examples.ai.common import ExampleProvider
from tkai.ai import ChatMessage, ChatRequest, ProviderManager


def run() -> str:
    """Return a normalized response from the default provider."""
    manager = ProviderManager()
    manager.register(ExampleProvider(), default=True)
    return manager.chat(ChatRequest((ChatMessage("user", "hello"),))).content


if __name__ == "__main__":
    print(run())
