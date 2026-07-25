"""Run a deterministic Agent with an explicitly injected local memory store."""

from tkai.sdk import Agent, MemoryRecord
from tkai.sdk.adapters import (
    InMemoryMemory,
    InMemoryProvider,
    ProviderAdapter,
    V1RuntimeAdapter,
)

memory = InMemoryMemory()
memory.put(MemoryRecord("session", "local context"))
provider = InMemoryProvider(responder=lambda request: request.options.get("memory", ""))
agent = Agent(V1RuntimeAdapter(ProviderAdapter(provider), memory=memory))
print(agent.chat("hello", memory_key="session").output)
