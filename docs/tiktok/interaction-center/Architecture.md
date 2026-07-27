# TikTok AI Interaction Center

## Architecture

The Interaction Center is a tenant- and workspace-isolated control plane. Projects own
versioned drafts and tasks. Drafts may use localized reply, comment, or message
templates. Reviews gate every queue operation. Priority, workspace, delayed, and retry
queues are logical views over the shared task store; the platform Workflow, Automation,
Audit, Metrics, and Observability services remain the infrastructure owners.

Bounded ports connect Account Center, Browser Runtime, Proxy Center, Content Center,
Publishing Center, and Data Collection Center. Default ports are deterministic mocks
and never access TikTok.

## Lifecycle

`Draft → Review → Approved → Queued/Scheduled → Running → Completed/Failed → Archived → Deleted`

Rejected or edited drafts return to review. Failed tasks may enter the retry queue up
to their configured retry limit. Concurrency is enforced per service instance.

## Drafts and templates

Draft history records every content and variable revision. Templates support reply,
comment, and message kinds, localized content, declared variables, import, export, and
clone. Imported data is validated and contains no credentials.

## Review and approvals

Reviewers may approve, reject, or reapprove with notes. Expired reviews cannot approve
work. Queueing is denied unless the current draft version is approved. Every decision
is audited.

## Queues and analytics

Logical queues provide priority selection, workspace isolation, delayed execution, and
bounded retry. Analytics expose task volume, completion and failure rates, average
queue and execution times, trends, and Prometheus metrics.

## Security

Every operation applies RBAC plus tenant and workspace isolation. Approval enforcement
is mandatory. Audit events contain identifiers, never draft content or secrets.
Metadata rejects credential-like keys. The module provides no unsolicited bulk
messaging, engagement manipulation, CAPTCHA bypass, restriction bypass, or
platform-security bypass.

## Operations guide

Monitor `/tiktok/interaction/metrics` and `/tiktok/interaction/dashboard`. Alert on
failure rate, retry growth, queue age, and concurrency saturation. Operators should
archive completed projects according to retention policy and investigate failures
through audit references and shared observability.

## Windows deployment guide

Use the repository Python environment, install the existing server extras, and start
the normal TKAI API service. No Interaction Center-specific daemon or secret is
required. Build `dashboard/frontend` and `studio/frontend` with their existing npm
production build commands. Deploy with the existing Docker Compose or Kubernetes
manifests; do not add a separate interaction workload.
