# TKAI 2.0 RC-1 SDK Integration Baseline

## Scope

This baseline validates the additive TKAI 2.0 developer SDK layers without
changing V1.x Runtime behavior or enabling production integrations. It covers
the explicit Agent adapter, workflow reference runtime, Tool SDK, Provider SDK,
Memory SDK, and Plugin Runtime.

## Validation

- Agent `chat`, `run`, `call`, and bounded synchronous `stream` paths use an
  explicitly injected local V1 runtime adapter and reference provider.
- Workflow execution composes local Agent and Tool calls.
- Reference memory is injected into Tool and Plugin contexts.
- Reference Provider, Memory, Tool, Workflow, and Plugin lifecycles and
  failures remain isolated to their owning local objects.
- Registry, factory, workflow, tool, plugin, provider, and memory coverage is
  offline, bounded, and thread-safe.
- SDK examples are smoke-tested with no credentials, network access, or user
  configuration.

## Compatibility

V1.x Runtime and public APIs remain unchanged. Existing Agent, SDK adapter,
extension decorator, provider, memory, and workflow declaration import paths
remain supported. All SDK dependencies are explicit; no default provider,
network transport, persistent memory, or plugin discovery is enabled.

## Known limitations

The SDK remains reference-only: no real vendor provider adapters, distributed
workflow execution, persistent/vector memory, MCP, remote plugins, marketplace,
Studio, or Enterprise capabilities are included.
