"""Run a deterministic Agent with explicit local SDK dependencies."""

from tkai.sdk import Agent
from tkai.sdk.adapters import InMemoryProvider, ProviderAdapter, V1RuntimeAdapter

agent = Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider())))
print(agent.chat("hello").output)
