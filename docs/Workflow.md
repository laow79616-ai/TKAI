# Workflow Engine

A `Task` is a named callable that receives a mutable context. A `Step` wraps a
task with an optional condition, loop count, and retry count.

`WorkflowEngine.run(steps, context, mode)` supports `serial` and `parallel`
scheduling. The executor emits `step.skipped`, `task.started`, `task.completed`,
and `task.failed` through `EventBus`. Final task failures raise `WorkflowError`
with the original exception retained as its cause.

Parallel steps must not make unsynchronized writes to the shared context.

## Extended execution API

`WorkflowDefinition` and `Workflow` provide a typed, validated state machine:
`created → validated → pending → running`, followed by `completed`, `failed`,
`paused`, or `cancelled`. `WorkflowContext` keeps inputs, shared values, named
step results, and the previous result in memory; `WorkflowResult.to_dict()`
provides a serialization-safe recovery snapshot.

Steps can declare dependencies, enable flags, metadata, retry policy, timeout,
and `continue_on_error`. Handler return values may be synchronous or awaitable.
The executor emits both the legacy `task.*` events and `step.*` events; event
listener failures are isolated unless `fail_fast_events` is set.
