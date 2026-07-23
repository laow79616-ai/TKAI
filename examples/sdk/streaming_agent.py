"""Consume the bounded synchronous stream from the reference provider."""

from tkai.sdk import Agent
from tkai.sdk.adapters import InMemoryProvider, ProviderAdapter, V1RuntimeAdapter

agent = Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider())))
for response in agent.stream("hello"):
    print(response.output)
