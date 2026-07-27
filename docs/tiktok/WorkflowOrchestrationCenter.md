# TikTok Workflow Orchestration Center

## Architecture

The Workflow Orchestration Center is the TikTok Cloud Control Platform control
plane for approved multi-center workflows. It reuses the platform's Workflow,
Automation, Audit, Metrics, Observability, and Security components through
ports; it does not duplicate persistence, brokers, secret storage, telemetry,
or authentication infrastructure.

The domain package is `tiktok.workflow_center`. Its service owns workflow
definitions, templates, schedules, approval records, execution state, queues,
history projections, analytics, API contracts, and dashboard data. Node ports
connect only to the existing Account Center, Browser Runtime, Proxy Center,
AI Account Farming, Content Center, Publishing Center, Data Collection Center,
Interaction Center, and Risk Control Center.

No node may bypass a TikTok restriction, challenge, rate limit, health gate, or
risk decision. Production deployments must inject approved center adapters.
The default adapter is inert and intended for tests and local validation.

## Workflow lifecycle

The controlled lifecycle is:

`Draft -> Review -> Approved -> Ready -> Scheduled/Running -> Paused ->
Completed/Failed -> Archived -> Deleted`.

Approval is mandatory for `Review -> Approved`. Editing is limited to Draft
and Review; each update and transition increments or records a pinned version.
Deleted workflows are excluded from normal listings.

## Execution engine

Executions pin a workflow version and support sequential, parallel, and
conditional definitions. The current local engine deterministically executes
the graph's declared node list. Distributed workers can consume the same
contracts through the existing Automation and Workflow infrastructure.

Every successful step advances a checkpoint. Failed steps retry only up to the
node's bounded retry policy and then enter the retry queue. Paused or failed
executions resume from the checkpoint. Cancellation is cooperative. Rollback
calls the injected center ports in reverse completion order. Node timeouts and
workflow maximum runtime are validated bounds for worker enforcement.

## Queues

The service exposes execution, priority, retry, and delayed queues. Priority is
bounded from 0 through 100 and sorted highest first. Tenant and workspace
filters apply to all queue metrics. Production concurrency and durable delivery
reuse the platform's existing queue and event-streaming infrastructure.

## Scheduling

Schedules support immediate, one-time, recurring, and calendar modes, named
timezones, execution windows, and bounded maximum concurrent executions.
Calendar and recurring expressions are stored as scheduler-neutral contracts;
the existing scheduler validates and dispatches them in deployment.

## Approvals

Workflow approval, execution approval, and high-risk-step approval are distinct
gates. Approval records require a reviewer and future expiration. Decisions
record the operator and note in the audit timeline. Expired or rejected
approvals cannot authorize execution.

## Conditions

Conditions cover success, failure, threshold, health, risk score, time window,
workspace state, and account state. Operators are restricted to equality and
ordered comparisons. Incoming execution context is data only; arbitrary code
or expression evaluation is not supported.

## Variables

Workflow, environment, and runtime variables are validated before enqueue.
Sensitive values must be indirect `secret://` references resolved by the
existing security/secret infrastructure. Passwords, tokens, cookies, sessions,
credentials, and secrets are rejected from metadata and node configuration.

## Analytics

Analytics include workflow runs, success and failure rates, average runtime,
retry count, queue time, and average step duration. Prometheus output exposes:

- `tiktok_workflows_total`
- `tiktok_workflow_executions_total`
- `tiktok_workflow_success_total`
- `tiktok_workflow_failures_total`
- `tiktok_workflow_retry_total`
- `tiktok_workflow_latency_seconds`

## Security

Every operation requires tenant, workspace, actor, and RBAC scope. Reads and
writes enforce tenant and workspace isolation. Approval enforcement occurs at
workflow promotion, execution enqueue, and every manual/high-risk step. Audit
events contain references and decisions, never secrets. Logs and adapters must
preserve the same rule.

## Operations guide

1. Configure the platform's existing authentication, RBAC, audit, metrics,
   observability, queue, scheduler, and encrypted-reference providers.
2. Inject approved node adapters for the nine existing TikTok centers.
3. Monitor queue depth, failure rate, retry count, and latency metrics.
4. Alert on approval backlogs, retry growth, stale schedules, and risk-control
   pauses.
5. Pause dispatch before maintenance, drain running work, checkpoint, deploy,
   validate health, and resume.
6. If TikTok reports a restriction or challenge, stop affected work and route
   it to Risk Control and manual review. Never automate around it.

API resources are rooted at `/tiktok/workflows`, with templates, executions,
queues, schedules, history, analytics, dashboard, and metrics subresources.

## Windows deployment guide

From PowerShell with Python and Node.js installed:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pytest
npm --prefix dashboard\frontend run build
npm --prefix studio\frontend run build
```

Use the existing Windows service/container deployment scripts and provide
configuration through environment variables or encrypted references. Do not
place secrets in source, workflow metadata, command lines, or log files.
