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
