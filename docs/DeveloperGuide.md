# TKAI Platform Developer Guide

## SDK composition

Use public `tkai.sdk` contracts and inject all execution dependencies. An
`Agent` delegates through an explicit adapter; it does not create a Provider or
read an API key implicitly.

```python
from tkai.sdk import Agent
from tkai.sdk.adapters import InMemoryProvider, ProviderAdapter, V1RuntimeAdapter

agent = Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider())))
print(agent.chat("hello").output)
```

Reference providers and memories are deterministic local implementations for
examples and tests, not production provider integrations.

## Workflows, tools, providers, memory, and plugins

- Define workflows with the SDK Workflow contracts and explicitly supplied
  execution context. See [Workflow SDK](WorkflowSDK.md).
- Define and register local tools with the [Tool SDK](ToolSDK.md).
- Implement provider contracts, configuration, capabilities, and lifecycle via
  the [Provider SDK](ProviderSDK.md).
- Use the bounded reference implementation and contracts in the
  [Memory SDK](MemorySDK.md); Redis/vector/semantic memory are not included.
- Compose local extensions through the [Plugin SDK](PluginSDK.md), retaining
  explicit lifecycle and dependency resolution.

## Studio integration

Studio is a consumer of the SDK, not a replacement Runtime. Its backend uses
`SDKStudioGateway`, while Workflow Designer, Execution Monitor, and Agent Chat
are reference product contracts. Do not bypass the frozen Studio REST contract
or import Runtime internals from Studio code.

## Enterprise reference foundations

Use Enterprise descriptors and reference services through explicit dependency
injection. They describe identity, organization, tenant, authorization, audit,
and license boundaries but do not authenticate users, persist data, or enforce
decisions. Do not add Runtime, SDK, or Studio hooks merely by importing an
Enterprise package.
