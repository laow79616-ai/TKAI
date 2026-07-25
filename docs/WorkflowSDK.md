# TKAI 2.0 Workflow SDK

## Architecture

`tkai.sdk.workflow` keeps the existing immutable `Node`, `NodeKind`, and
`WorkflowDefinition` declarations compatible while adding `WorkflowRuntime` as
an explicit, synchronous reference executor. It does not alter the V1.x
workflow runtime.

## Runtime and context

`WorkflowRuntime` executes only a caller-provided definition. `ExecutionContext`
holds explicitly injected variables, memory, provider, agent, metadata,
cancellation event, timeout, and application context. The runtime never creates
providers, reads configuration, starts a worker thread, contacts a network
service, or persists a workflow.

## Execution model

The reference runtime supports task, condition, loop, retry, parallel, branch,
sequence, and end nodes. Control behavior is deterministic: conditions and
loops select the first or second successor, branches select a named or indexed
successor, retries use the node's bounded `attempts` metadata, and parallel
branches run sequentially in declaration order. This is deliberately not a
distributed scheduler.

## Lifecycle, snapshots, and hooks

`execute`, `step`, `resume`, `cancel`, `snapshot`, and `restore` provide a
bounded in-memory reference lifecycle. Snapshots are defensive copies and are
not durable checkpoints. Hooks define before/after execution, before/after
node, error, and telemetry observation contracts; hook failures are isolated.

## Reference tasks

`EchoTask`, `DelayTask`, `ConditionTask`, and `ReferenceMemoryTask` make local
examples and tests readable. `DelayTask` is only a duration marker and does
not sleep. `ReferenceMemoryTask` requires an explicitly injected compatible
memory object.

## Current limitations

There is no persistent workflow state, cron scheduling, DAG visualization,
distributed execution, real parallel worker execution, or workflow UI. The
reference runtime is not a production orchestrator.
