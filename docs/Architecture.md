# TKAI V1.0 Architecture

TKAI is organized as independent layers with one-way dependencies: commands
call generators, templates, configuration, and framework services; framework
services depend only on `tkai.core`. This prevents command/UI imports from
forming runtime cycles with domain services.

```text
commands → generators/templates/config → core
plugins, workflow, ai                → core
```

The workflow layer depends only on core exceptions and typed local models.
Its executor owns retry and timeout mechanics, while the scheduler retains the
compatible serial/parallel facade. This keeps workflows independent of plugins
and provider implementations.

The public package APIs are exposed from each package's `__init__.py`; legacy
paths such as `tkai.template_engine.TemplateManager` remain compatibility
imports for the canonical template manager.

## Workflow runtime

`WorkflowEngine` is a public facade. `WorkflowRuntime` owns execution state,
`Dispatcher` owns stable dependency-ready queues, `Executor` owns a single
step invocation, and `CheckpointManager` serializes runtime state. The CLI
only invokes the facade and does not import scheduler internals, avoiding a
reverse dependency from commands into runtime control.

## AI providers

The AI layer is independent of workflow runtime internals. `ProviderManager`
routes normalized requests to provider adapters; adapters return TKAI models,
not third-party SDK objects. Optional SDKs are lazy imports.

The provider subsystem has one-way internal dependencies:

```text
tkai ai CLI → AICommandService → DoctorService / ProviderManager / FallbackEngine
ProviderManager → ProviderRegistry → AIProvider
OpenAI-compatible provider → RuntimeAdapter → ProviderRuntime → AsyncTransport
```

Capability routing lives in `ProviderManager` and consumes typed capability
declarations held by `ProviderRegistry`; it does not depend on fallback.
`FallbackEngine` consumes an already ordered, capability-filtered candidate
list and has no dependency on the manager. `DoctorService` is read-only and
inspects these layers without sending requests or changing lifecycle state.
This separation keeps command imports from reversing runtime dependencies.
