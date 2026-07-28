# Enterprise TikTok AI Task Scheduler

## Architecture and integrations

The scheduler is a single-user, local control-plane service. It coordinates bounded
tasks through reference-only ports for Account Center, Browser Cluster and Runtime,
Device Center, Proxy Center, Workflow Center, Publishing, Collection, Interaction,
Risk, Operations, Analytics, and Local Runtime. The default port is a deterministic
test double and makes no live TikTok request. Shared audit, metrics, workflow,
observability, security, event, and recovery infrastructure remains authoritative;
the scheduler does not duplicate it.

## Lifecycle, task types, queues, and priorities

Tasks move through Draft, Pending Approval, Ready, Scheduled/Queued, Allocated,
Running, Paused/Retrying/Recovering, and a terminal Completed, Failed, or Cancelled
state before archival/deletion. Transitions are validated. Only the documented
bounded task types are accepted; custom bounded tasks require a registered handler
reference and payloads cannot contain code, commands, scripts, shells, executables,
cookies, sessions, credentials, or secrets.

Queues are tenant/workspace namespaced. The service supports global, workspace and
resource-oriented queue names plus publishing, collection, interaction, retry,
delayed, recovery, and dead-letter queues. Priority is bounded to 1–100 with named
Background, Low, Normal, High, and Critical values. Age increases effective
priority up to 100, preventing starvation. Workspace rotation, queue depth admission,
resource caps, worker capacity, and concurrency limits provide fairness and
backpressure.

## Scheduling and dependencies

Immediate, one-time, recurring, interval, calendar-window, event-triggered, and
dependency-triggered schedules carry timezone, start/end, maximum-run, and
missed-run policy data. Interval and run bounds are validated. Dependencies can
require success, completion, or be optional; parallel intent and timeout are
recorded. Graph insertion performs cycle and maximum-depth checks.

## Allocation, workers, execution, and checkpoints

Local workers advertise type, capacity, health, supported task types, and workspace
scope. Dispatch validates gates, chooses an eligible worker, reserves reference-only
resources with an expiry, and releases them on every outcome. Execution performs
approval and restriction/challenge checks before adapter preflight and execution,
supports cancellation/graceful stop, persists outcomes, and records telemetry.

Checkpoints contain JSON-safe state, completed/pending steps, resource references,
retry position, expiry, and SHA-256 integrity. Resume revalidates scope, expiry,
integrity, recovery count, and restriction/challenge state before requeueing.

## Retries, failures, and recovery

Retry policy bounds attempts and delays, supports exponential backoff and cooldown,
and lists eligible failure categories. Exhausted or ineligible work enters the
dead-letter queue. Recovery supports checkpoint resume and reference-based resource,
browser, device, proxy, and workflow adapters. It stops when a TikTok restriction
or challenge remains unresolved and never attempts CAPTCHA bypass or circumvention.

## Limits, safety, and security

Global/workspace/resource task counts, concurrent executions, queue depth, retries,
runtime, payload size, dependency depth, reservation time, and recovery attempts are
positive bounded values. A kill switch, manual cancellation, workspace/account/
feature pauses, approval gates, and risk metadata enforce safe operation.

Every read/write is tenant and workspace isolated and RBAC protected. Payloads are
JSON-safe and size-limited. References must point to encrypted credential stores;
plaintext cookies, sessions, proxy credentials, or secrets are rejected and never
logged. The feature offers no CAPTCHA bypass, restriction circumvention, security
bypass, anti-detection guarantee, spam automation, or engagement manipulation.

## Telemetry, statistics, dashboard, and API

Prometheus output includes all `tiktok_scheduler_*` counters/gauges required by the
feature specification. The statistics surface reports volume, rates, timing,
concurrency, utilization, and task distribution. The dashboard exposes Scheduler
Overview, Tasks, Queues, Schedules, Dependencies, Allocations, Workers, Executions,
Checkpoints, Retries, Failures, Recovery, Limits, Telemetry, and Statistics.

Read APIs are rooted at `/tiktok/task-scheduler/` and include every specified
resource plus `/dashboard` and `/metrics`. Route registration remains
transport-neutral and can be attached to the existing FastAPI host.

## Operations and Windows local guide

1. Activate `.venv\Scripts\Activate.ps1`.
2. Configure only encrypted-store references; do not put credentials in task JSON.
3. Register bounded local workers and verify healthy heartbeats.
4. Review limits, approval gates, and risk policy before clearing workspace pause.
5. Monitor queue depth, worker utilization, retry/recovery, and dead-letter metrics.
6. Use the kill switch or workspace pause for incidents; use cancellation for a
   graceful individual stop.
7. Resolve TikTok restrictions/challenges manually before any recovery attempt.
8. Run `python -m pytest tests/tiktok/test_task_scheduler.py`, Ruff, mypy, and both
   frontend production builds before release.
