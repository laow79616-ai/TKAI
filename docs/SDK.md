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

## Compatibility

`tkai.sdk` is isolated from V1.x runtime implementations and does not alter
their public APIs. Future adapters may explicitly use existing provider,
workflow, configuration, plugin, or distributed services.

## Next sprint

Implement V1.x runtime adapters and in-memory reference implementations behind
these contracts, then add end-to-end SDK examples. Web UI, Studio, and
Enterprise capabilities remain out of scope.
