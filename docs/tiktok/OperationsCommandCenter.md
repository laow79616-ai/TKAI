# TikTok Operations Command Center

## Architecture

`tiktok.operations_center` is the tenant- and workspace-isolated operational
control plane for the existing TikTok centers. It owns operational projections,
tasks, alerts, incidents, health, recovery records, activity, and audit records.
Bounded ports connect Account Center, Browser Runtime, Proxy Center, Account
Farming, Content, Publishing, Data Collection, Interaction, Risk Control, and
Workflow Orchestration. It does not duplicate their storage or infrastructure.

## Lifecycle and overview

Centers move through Draft, Active, Maintenance, Paused, Recovering, Archived,
and Deleted states using validated transitions. The overview aggregates account,
browser, proxy, workflow, task, publishing, collection, interaction, alert, and
incident counts. Unified status remains a projection of source-module state.

## Control actions

Every action requires `tiktok:operations:control` (or admin), is bounded to an
approved TikTok module, and produces activity and audit records. High-risk
actions additionally require a current tenant/workspace-scoped approval.
Manual stop, workspace/feature pause, account pause, and the kill switch are
first-class actions. A kill switch blocks mutation while retaining health and
incident access.

## Tasks, alerts, and incidents

Tasks support manual, scheduled, workflow, publishing, collection, interaction,
and recovery kinds with bounded priorities, timeouts, and retry counts. Alerts
carry severity, category, source, acknowledgement, escalation, resolution, and
history. Incidents include impact, relationships, timeline, recovery plan,
resolution, and postmortem references.

## Health and recovery

Health combines account, browser, proxy, session/source-module, publishing,
collection, interaction, workflow, and risk projections into a composite score.
Recovery uses references only, enforces attempt and cooldown bounds, and stops
without attempting recovery whenever a TikTok restriction or unresolved
challenge remains. Manual approval is enforced where configured.

## Activity and audit

The live activity feed distinguishes user and system action categories and can
be searched or filtered by consumers. Audit records contain actor, action,
resource and state references, reason, approval reference, timestamp, and
correlation ID. Cookies, sessions, credentials, tokens, and secrets are rejected
from metadata and must never be written to logs or audit records.

## Integrations and security

Adapters reuse existing Command Center, Workflow, Automation, Security, Audit,
Metrics, Event Streaming, and Observability capabilities. Production adapters
must enforce tenant/workspace isolation, RBAC, approval gates, command
authorization, encrypted references, and risk policy. There is no CAPTCHA
bypass, platform-security bypass, restriction circumvention, or evasion logic.

## Operations guide

1. Confirm tenant, workspace, actor, permission, and current platform health.
2. Open or link an incident for degraded or restricted states.
3. Prefer pause/stop actions; obtain approval before any high-risk action.
4. Do not resume recovery while restrictions or unresolved challenges remain.
5. Validate correlation IDs in activity, audit, metrics, and observability.
6. Use the kill switch when safe bounded operation cannot be guaranteed.

## Windows local operations guide

From PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_operations_center.py
.\.venv\Scripts\python.exe -m ruff check tiktok\operations_center tests\tiktok\test_operations_center.py
.\.venv\Scripts\python.exe -m mypy
npm --prefix dashboard\frontend run build
npm --prefix studio\frontend run build
git diff --check
```

Tests use bounded doubles and never require live TikTok access.
