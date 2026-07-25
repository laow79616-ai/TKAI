"""Default and explicit-provider routing example without network access."""

from __future__ import annotations

from examples.ai.common import ExampleProvider
from tkai.ai import ChatMessage, ChatRequest, ProviderManager


def run() -> tuple[str, str]:
    """Return results from default and explicit provider routes."""
    manager = ProviderManager()
    manager.register(ExampleProvider("primary"), default=True, aliases=("main",))
    manager.register(ExampleProvider("secondary"))
    request = ChatRequest((ChatMessage("user", "hello"),))
    primary = manager.chat(request).content
    secondary = manager.chat(request, provider="secondary").content
    return primary, secondary


if __name__ == "__main__":
    print(run())
