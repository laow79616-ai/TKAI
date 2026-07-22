# Workflow Engine

A `Task` is a named callable that receives a mutable context. A `Step` wraps a
task with an optional condition, loop count, and retry count.

`WorkflowEngine.run(steps, context, mode)` supports `serial` and `parallel`
scheduling. The executor emits `step.skipped`, `task.started`, `task.completed`,
and `task.failed` through `EventBus`. Final task failures raise `WorkflowError`
with the original exception retained as its cause.

Parallel steps must not make unsynchronized writes to the shared context.
