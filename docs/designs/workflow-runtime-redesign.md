# Workflow Runtime Redesign

## Purpose

Replace the internal workflow runtime while preserving all public APIs:
`Workflow`, `WorkflowEngine`, `Task`, `Step`, `StepResult`, `WorkflowResult`,
`Executor`, and `Scheduler`. Existing synchronous callers continue to use
`WorkflowEngine.run()` and `WorkflowEngine.execute()` unchanged.

## Why the current runtime cannot provide complete recovery

The current implementation spreads execution state across `WorkflowEngine`,
`Scheduler`, and `Executor`. `Scheduler` owns parallel dispatch, while the
engine owns dependency iteration and the executor owns retries. No single
runtime object owns the authoritative pending/running/completed step sets.
Consequently, a snapshot can preserve values but cannot precisely resume the
dispatch plan, prevent already-completed work from running again, or safely
apply pause/cancel between scheduling decisions.

The synchronous compatibility path also uses a thread-pool scheduler, while
async execution is a separate path. This prevents one consistent model for
parallelism, cancellation, retry, timeout, and stable result ordering.

## Module layout

```text
workflow/
  runtime.py       Runtime coordinator and compatibility adapters
  dispatch.py      Ready-queue, dependency graph, serial/async-parallel dispatch
  control.py       Pause, resume, cancel, and cooperative checkpoints
  checkpoint.py    Immutable execution snapshot and in-memory store
  recovery.py      Snapshot validation and resume-plan construction
  executor.py      One-step invocation, timeout, retry, and event emission
  scheduler.py     Deprecated-compatible facade delegating to Runtime
```

`WorkflowEngine` is a facade only: it creates/configures a `WorkflowRuntime`
and translates legacy return shapes. The runtime is the only owner of mutable
execution state. `Dispatcher` owns the dependency graph and ready queue;
`Scheduler` is a compatibility facade that delegates to the dispatcher;
`Executor` owns only one-step invocation, retry, timeout, and event emission.

## State machine

Workflow transitions remain:

```text
created -> validated -> pending -> running
running -> paused | completed | failed | cancelled
paused  -> running | cancelled
```

The implementation makes those user-facing transitions cooperative through an
internal control state machine:

```text
pending -> running -> pausing -> paused -> resuming -> running
                  \-> cancelling -> cancelled
                  \-> completed | failed
```

Every edge is validated. A pause request stops dequeuing work only after any
currently claimed step finishes; a cancel request closes the ready queue and,
for native asyncio work, cancels active tasks. Synchronous and threaded
handlers are never forcefully killed. They may call `runtime.checkpoint()` and
return early when it reports a pause or cancellation request.

The runtime additionally tracks each step as `pending`, `running`, `skipped`,
`completed`, or `failed`. A transition is checked centrally before every
dispatch decision. `pause` is a cooperative control signal: running steps may
finish, but the dispatcher cannot dequeue a new step until `resume`. `cancel`
closes the ready queue immediately, cancels not-yet-started async work, and
records a cancelled snapshot. These are dispatch operations, not setters.

## Scheduling model

The dispatcher maintains a stable topological ready queue ordered by original
definition index. Serial mode dispatches one ready step at a time. Parallel
mode schedules only ready steps with `asyncio.create_task` bookkeeping and an
`asyncio.Semaphore(max_parallelism)`. This supports Python 3.10 and does not
require `asyncio.TaskGroup`.

Results are stored by definition index, so output ordering is deterministic
even when completion order differs. With `fail_fast=true`, the first terminal
failure cancels unscheduled and cancellable work. With `fail_fast=false`, the
runtime records all failures and continues steps whose dependencies succeeded
or explicitly allow continuation.

`Dispatcher.claim()` records an in-flight step before a task is created. This
prevents duplicate scheduling and gives the dispatcher one consistent control
boundary for serial and parallel paths. Resume reconstructs terminal sets and
then starts from the same ready queue; completed and skipped steps are never
claimed again.

## Recovery model

A `Checkpoint` contains the workflow definition identity, lifecycle status,
typed input/shared context, named step results, completed/skipped/failed step
sets, pending queue, stable ready ordering, and execution options. It is
serialized as plain JSON-safe data and stored by an `InMemoryCheckpointStore`.

Recovery validates that the definition identity and step names match, restores
the context and terminal step results, rebuilds the dependency graph, and
schedules only pending steps. Completed and skipped steps are never invoked
again. Failed and cancelled states remain terminal unless the caller explicitly
starts a new workflow instance from an approved checkpoint policy.

## Design review

1. **No cycle or overlap:** Runtime owns mutable state; Dispatcher owns
   readiness; Checkpoint owns data; Recovery owns plan reconstruction. None
   imports `WorkflowEngine`.
2. **Clear boundaries:** Scheduler and Executor are compatibility/service
   facades, never competing state owners.
3. **Facade-only engine:** WorkflowEngine cannot inspect queues or decide
   retries; it delegates every execution decision to Runtime.
4. **Real control:** Dispatcher checks pause/cancel before every dequeue, so
   they prevent later dispatch rather than merely changing a model field.
5. **Real recovery:** the step terminal sets and ready ordering reconstruct a
   pending execution plan; recovery is not context-only restoration.
6. **Unified core:** serial is the same dispatcher with concurrency one;
   parallel only changes the concurrency permit count.
7. **Compatibility:** all listed public types and legacy return shapes remain;
   runtime types are internal or additive.
8. **Extensibility:** Agent, Memory, Tool, and Automation attach through typed
   context/services and handlers, not reverse imports into runtime internals.

## Backward compatibility

- Existing `Task` and `Step` fields retain their meaning; new runtime fields
  are internal adapters or additive optional fields.
- `Executor.execute()` continues returning the legacy list-of-values result.
- `Scheduler.run()` continues accepting `serial` and `parallel` modes.
- `WorkflowEngine.run()` continues returning grouped results.
- Existing `EventBus` event names stay available; richer runtime events are
  additive.
- Old snapshots containing only context/results are upgraded into the new
  checkpoint format with unknown steps treated as pending.

## Migration and verification

Implementation will first add the runtime beside the current internals, route
the compatibility entry points through it, then remove duplicated internal
state only after old and new API regression tests pass. Tests will cover stable
async parallelism, fail-fast cancellation, pause/resume/cancel checkpoints,
recovery without duplicate execution, legacy facades, and serialization.
