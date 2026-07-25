"""Capability-constrained routing example without network access."""

from __future__ import annotations

from examples.ai.common import ExampleProvider
from tkai.ai import Capability, ChatMessage, ChatRequest, ProviderManager


def run() -> str:
    """Route only to a provider explicitly declaring tool-call support."""
    manager = ProviderManager()
    manager.register(ExampleProvider(), default=True)
    return manager.chat(
        ChatRequest((ChatMessage("user", "hello"),)),
        required_capabilities=(Capability.TOOLS,),
    ).content


if __name__ == "__main__":
    print(run())
