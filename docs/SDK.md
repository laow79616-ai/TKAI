# TKAI 2.0 SDK architecture

## Scope

The V2 SDK is an additive developer platform above the stable V1.x Runtime.
It does not change V1.x Runtime behavior, ProviderManager defaults, the
workflow executor, or optional distributed services.

## Package layout

```text
tkai.sdk
├── agent.py          # Agent facade and AgentRuntime adapter protocol
├── workflow.py       # Declarative Node and WorkflowDefinition graph
├── plugins.py        # @tool, @provider, @memory, @workflow registration
├── providers.py      # Provider protocol and capability metadata
├── memory.py         # Short/Long/Vector/Redis memory contracts
└── configuration.py  # Mapping, environment, and Python config sources
```

## Developer API

```python
from tkai.sdk import Agent, Node, NodeKind, WorkflowBuilder

# Applications supply an adapter over V1.x Runtime services.
agent = Agent(runtime=my_runtime_adapter)
reply = agent.chat("Hello")

workflow = (
    WorkflowBuilder("review")
    .add(Node("check", NodeKind.CONDITION, successors=("parallel",)))
    .add(Node("parallel", NodeKind.PARALLEL))
    .build()
)
```

`Agent()` can be constructed without configuration but raises a clear SDK error
when execution is requested before an explicit runtime adapter is supplied.

## Reference implementations

`V1RuntimeAdapter` composes an explicitly supplied `ProviderAdapter` and
optional `InMemoryMemory`. `InMemoryProvider` is a deterministic local provider
for examples and tests only: it never reads credentials, environment variables,
or network state. `InMemoryMemory` is bounded, thread-safe, namespace-aware,
and process-local; it is not Redis, vector, or production persistence.

Configuration loaders are explicit. `MappingConfigurationLoader` reads a passed
mapping, `EnvironmentConfigurationLoader` reads only an injected mapping and
prefix, and `CompositeConfigurationLoader` applies later source precedence.

## Streaming and errors

`Agent.stream()` forwards a synchronous provider iterator directly: it starts no
threads, does not buffer unbounded data, and preserves upstream failures as
`ProviderExecutionError` with the original exception as its cause. Invalid
requests raise `InvalidRequestError` before reaching the provider.

## Compatibility

`tkai.sdk` is isolated from V1.x runtime implementations and does not alter
their public APIs. Future adapters may explicitly use existing provider,
workflow, configuration, plugin, or distributed services.

Provider contracts are documented separately in [Provider SDK](ProviderSDK.md).
Memory contracts are documented separately in [Memory SDK](MemorySDK.md).
Reference execution is documented separately in [Workflow SDK](WorkflowSDK.md).
Reference tools are documented separately in [Tool SDK](ToolSDK.md).

## Current scope

V1.x runtime adapters and in-memory reference implementations are available
through explicit dependency injection. Workflow execution, production provider
adapters, Web UI, Studio, and Enterprise capabilities remain out of scope.
