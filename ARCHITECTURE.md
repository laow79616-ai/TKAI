# TKAI Architecture

## V9 production architecture

V9 is an additive, authenticated, read-only advisory layer composed of exactly
ten completed adaptive components. The Adaptive Meta-Kernel supplies stable
registration and compatibility contracts; the nine meshes cover intelligence,
governance, knowledge, reasoning, decision, planning, operations, recovery,
and compatibility. V9 components project metrics, logs, traces, diagnostics,
health, audit, and dashboard metadata without mutating V6–V8 framework state,
TikTok business state, configuration, storage, schedules, workflows, or
recovery state. See `docs/v9/README.md` for the final component inventory.

## V7 production architecture

V7 is an opt-in framework layer under `tkai.v7`. The V6 runtime and TikTok
business modules retain their existing imports and behavior. Framework
dependencies point inward to stable contracts; no V7 package is auto-registered
or started by import. See `docs/v7/Architecture.md` and
`docs/v7/FrameworkOverview.md` for the verified framework map.

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
