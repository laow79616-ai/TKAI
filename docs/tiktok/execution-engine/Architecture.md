# TikTok AI Execution Engine Architecture

The engine is a local, single-user orchestration boundary between approved Operations Planner output and existing TikTok infrastructure. It owns execution state, stages, verification records, opaque result references, checkpoints, rollback coordination, monitoring, analytics, and audit. It does not own browser, device, account, proxy, resource, queue, worker, runtime, workflow, automation, or risk infrastructure.

## Integration boundary

All work passes through `ExecutionInfrastructurePort`. Production composition injects adapters for the Operations Planner, Automation Engine, Runtime Manager, Resource Center, Task Scheduler, Browser Cluster, Device Center, Account Center, Proxy Center, Workflow Center, and Risk Control Center. The local default is an offline mock and performs no TikTok network access.

Plan and result references are converted into tenant/workspace-bound opaque references. Metadata and audit records reject secret-bearing fields.

## Lifecycle and stages

The lifecycle is Pending, Validated, Queued, Dispatching, Running, Paused, Checkpointed, Recovering, Completed, Failed, Rolled Back, Archived, and Deleted. Invalid transitions fail closed.

Every execution exposes Validation, Preparation, Resource Allocation, Dispatch, Execution, Verification, Completion, and Cleanup stages.

## Pipelines

Sequential, parallel, conditional, checkpointed, retryable, and recoverable pipeline types share the same bounded step contract. Pipelines are capped at 100 steps, concurrency at 10, and attempts at 3. Parallel is a scheduling declaration: actual concurrency remains owned by the existing scheduler and worker infrastructure.

## Verification and rollback

Before queue admission, approval, risk, resource, runtime, dependency, and workspace validations must all pass. A failure prevents dispatch.

Rollback works backward over successful step results and invokes only declared rollback actions. It coordinates checkpoint rollback, resource release, queue cleanup, worker cleanup, runtime cleanup, and records an audit event.

## Monitoring and analytics

Monitoring reports execution health, stage progress, resource usage, runtime status, failure detection, and recovery status. Analytics reports success, failure, average runtime and recovery, rollback count, and resource consumption. Prometheus metrics are exposed under `/tiktok/execution/metrics`.

## Safety boundary

The engine does not implement CAPTCHA handling, restriction circumvention, security bypasses, anti-detection guarantees, spam, or unrestricted mass actions. Restriction and approval failures stop execution.
