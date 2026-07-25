# Workflow Runtime

## Adaptive runtime scheduler

`RuntimeScheduler` is an explicit, local provider-name scheduler. It does not
invoke providers or take over ProviderManager. Registered metadata and observed
result signals support round-robin, weighted round-robin, least latency, least
error, lowest cost, highest score, sticky-session, and adaptive selection.
It reuses the existing CircuitBreaker states and records optional Telemetry
metrics. Health, retry, service-discovery, and failover integrations remain
caller-controlled adapters; no network probes or service calls are started.

## Runtime architecture

`WorkflowEngine` is the compatibility facade. `WorkflowRuntime` owns mutable
execution state and `ExecutionContext`; `Dispatcher` owns the pending,
ready, completed, and in-flight queues. `Executor` invokes one step, while
`Scheduler` preserves the legacy serial/parallel API and provides native
asyncio dispatch for controlled parallel work.

## Dispatcher and execution state

Dispatcher readiness is a stable topological order. `claim()` makes a ready
step in-flight before it is scheduled, preventing duplicate execution.
`ExecutionState` is validated across `pending`, `running`, `pausing`,
`paused`, `resuming`, `cancelling`, `cancelled`, `completed`, and `failed`.
Illegal transitions raise `ExecutionTransitionError`.

## Checkpoint and recovery

`CheckpointManager` stores JSON-safe in-memory snapshots and exports or
imports JSON. A snapshot contains workflow context, ready/waiting/running
queues, terminal step sets, retry counters, and retained step results.
Recovery rebuilds the dispatcher and never re-invokes completed or skipped
steps. A previously running step is treated as unfinished and is safely
re-scheduled.

## Pause, resume, and cancel

Pause is cooperative: running handlers may finish, but the dispatcher does
not claim another step. Resume works both with a paused runtime in the current
process and a paused checkpoint. Cancel removes waiting work immediately and
cancels active native asyncio tasks; completed results remain in the final
result and checkpoint. Handlers can call `runtime.checkpoint()` to detect a
pause or cancellation request at an application-defined safe boundary.

## Known limitations

Checkpoints are JSON/in-memory artifacts, not a durable distributed store.
Synchronous and threaded handlers cannot be forcibly stopped. Parallel steps
share mutable context, so parallel handlers should not perform unsynchronized
writes to shared values.

## Compatibility

Existing `Workflow`, `WorkflowEngine`, `Task`, `Step`, `StepResult`,
`WorkflowResult`, `Executor`, and `Scheduler` interfaces remain available.
Runtime, checkpoint, and recovery APIs are additive. Legacy synchronous
`WorkflowEngine.run()` and `WorkflowEngine.execute()` retain their result
shapes.
