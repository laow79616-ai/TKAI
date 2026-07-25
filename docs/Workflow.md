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

## Checkpoint

`CheckpointManager` keeps JSON-safe execution snapshots in memory. A snapshot
contains the workflow context, execution state, dispatcher ready and waiting
queues, running work, terminal step sets, retry counters, and step results.
Use `create_checkpoint(name, runtime)`, `export_checkpoint(name)`,
`import_checkpoint(name, data)`, and `load_checkpoint(name)` to move a
snapshot between in-process runtime instances. No database or background
service is required.

## Recovery and resume

`WorkflowEngine.resume(workflow, checkpoint)` rebuilds the dispatcher from a
checkpoint rather than merely restoring the context. Completed and skipped
steps are removed from the ready queue and are never invoked again; pending
steps retain definition order and continue with their saved inputs, shared
state, named results, and retry counters. The optional `mode="parallel"` and
`max_parallelism` arguments apply to the remaining work just as they do to a
fresh execution.

Failed and cancelled step records are retained in the snapshot. They are not
silently retried during recovery; a caller that wants a new attempt must create
a new workflow execution policy explicitly.

## Cooperative pause, resume, and cancel

Runtime control is cooperative: a pause request allows work already running to
finish, but prevents the dispatcher from claiming another step. The ready and
waiting queues remain intact and a paused runtime produces a checkpoint that
can be supplied to `WorkflowEngine.resume()`. In the same process, pass the
paused runtime as `WorkflowEngine.resume(workflow, runtime=runtime)`. Resume
restores or retains completed and skipped records, retry counters, queue order,
and the configured parallelism; only unfinished work is scheduled.

Cancellation prevents future dispatch immediately. In native asyncio parallel
execution, currently active tasks are cancelled and not-yet-started steps are
recorded as cancelled. Completed step results remain available in the final
`WorkflowResult` and checkpoint. Threaded or synchronous handlers are not
forcefully interrupted: they finish their current invocation before the
runtime closes the queue.

A long-running handler can cooperatively query `runtime.checkpoint()`. It
returns `False` after a pause or cancellation request, allowing the handler to
return early at a safe application-defined boundary.

| Internal state | Permitted next states |
| --- | --- |
| `pending` | `running`, `cancelled` |
| `running` | `pausing`, `cancelling`, `completed`, `failed` |
| `pausing` | `paused`, `cancelling` |
| `paused` | `resuming`, `cancelling` |
| `resuming` | `running`, `cancelling` |
| `cancelling` | `cancelled` |
| `cancelled`, `completed`, `failed` | terminal |

## Command line

The workflow CLI exposes built-in definitions without requiring a network or
external service:

```bash
tkai workflow list
tkai workflow info hello-workflow
tkai workflow validate serial-example
tkai workflow run hello-workflow --input '{"name": "TKAI"}' --json
tkai workflow run hello-workflow --input-file input.yaml
tkai workflow checkpoint serial-example --output serial.checkpoint.json
tkai workflow resume serial-example --checkpoint serial.checkpoint.json --json
tkai workflow doctor
```

`checkpoint` writes a paused JSON snapshot before execution. `resume` imports
that snapshot and executes only work that remains pending. Commands return a
non-zero exit status for invalid input, unknown workflow names, validation
failures, or non-completed workflow results.
