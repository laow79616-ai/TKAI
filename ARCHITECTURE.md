# TKAI Architecture

## Layers

```text
CLI / Commands
        |
Core ─ Config ─ Templates ─ Generators
        |
Plugins       Workflow       AI
```

`tkai.core` contains domain-neutral runtime primitives. Configuration extends
the core `Settings` implementation with YAML persistence. Template and
generator services build projects without depending on command modules.

## Plugin framework

`PluginDiscovery` scans a plugin root for `plugin.json` manifests.
`PluginLoader` resolves a local `module:Class` entry. `PluginRegistry` owns
registered instances and metadata. `PluginManager` coordinates loading and the
`activate`/`deactivate` lifecycle against a `Context`.

## Workflow engine

`Task` contains work; `Step` adds condition, loop, and retry policy.
`Executor` executes steps and emits events. `Scheduler` chooses serial or
thread-based parallel execution. `WorkflowEngine` composes these services.

## AI framework

`AIClient` routes requests through `ProviderRegistry` to an `AIProvider`.
Providers normalize responses into `AIResponse`; network SDKs are injected as
completion clients so framework code remains provider-neutral.
