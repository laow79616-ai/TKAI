# TikTok AI Publishing Center

## Architecture

The Publishing Center is a tenant- and workspace-isolated control plane. Jobs,
queues, schedules, approvals, retries, history, failures, analytics,
notifications, and dashboard projections live in `tiktok/publishing_center`.
Existing Content Center, Account Center, Browser Runtime, Proxy Center, and
Account Farming services are consumed through bounded ports. Workflow,
Automation, Metrics, Audit, and Observability remain shared platform concerns
and are not duplicated.

No component bypasses or claims to bypass TikTok restrictions, platform
security, CAPTCHA, rate limits, or anti-abuse systems. The browser publisher
delegates only to an existing supported runtime operation. Tests use mocks and
never contact TikTok.

## Publishing lifecycle

The guarded lifecycle is Draft → Approved → Queued or Scheduled → Publishing →
Published or Failed. Jobs may be Paused or Cancelled where allowed and terminal
records may be Archived then Deleted. Every transition increments the version
and produces status history plus an audit event.

## Queue and scheduler

Queue projections support FIFO, priority, workspace, account, retry, and
delayed ordering. The scheduler supports immediate, one-time scheduled,
recurring, and calendar-window modes with IANA timezones, publishing windows,
maximum parallel jobs, and missed-schedule policy. Global concurrency is
enforced by the service; deployments should also enforce account-level limits
in the existing Workflow/Automation runtime.

## Approvals

When approval enforcement is enabled, only an active approval permits
enqueueing. Reviewers can approve, reject with notes, expire approvals, and
reapprove drafts. RBAC permission `tiktok:publishing:approve` (or admin) is
required and all actions are audited.

## Retries and failures

Retry policy defines maximum attempts, base delay, exponential backoff,
retryable failure categories, and automatic retry. Operators can manually retry
or recover failures with appropriate RBAC. Categories cover validation, media,
browser, proxy, session, timeout, cancellation, and unknown failures.

## History and analytics

History records the execution timeline, statuses, operator, job version, and
safe event details. Analytics expose publishing volume, success/failure rate,
retry count, queue time, execution time, and a daily report. Prometheus metrics:

- `tiktok_publish_jobs_total`
- `tiktok_publish_queue_total`
- `tiktok_publish_success_total`
- `tiktok_publish_failure_total`
- `tiktok_publish_retry_total`
- `tiktok_publish_latency_seconds`

## Security

Every read and mutation checks tenant, workspace, and RBAC scope. Approval is
enforced before queueing. Metadata rejects secret-bearing keys, exception
details are sanitized, and audit events contain references rather than
credentials. Operators must use external secret stores and the platform's
existing Security and Audit services.

## Operations guide

Monitor queue depth, failure rate, retries, and latency. Investigate categorized
failures through the dashboard and existing Observability stack. Pause affected
workspaces through existing controls, recover the underlying Account, Browser,
Proxy, Session, or Media issue, then use audited manual retry. Never work around
TikTok controls; cancelled or restricted operations must remain stopped.

## Windows deployment guide

Use PowerShell from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_publishing_center.py
.\.venv\Scripts\python.exe -m server
```

Build the dashboard with `npm run build` in `dashboard/frontend`. Configure
tenant, workspace, RBAC, audit, metrics, and secret-store integrations through
the existing deployment configuration. Do not place credentials in environment
files committed to source control. Docker and Kubernetes deployments use the
existing platform manifests and observability stack.
