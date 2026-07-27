# Enterprise TikTok AI Account Farming

## Architecture

Account Farming is a tenant- and workspace-scoped control plane for safe,
bounded, reviewable TikTok account activity. It reuses Account Center, Browser
Runtime, Proxy Center, workflow, automation, audit, RBAC, metrics, and
observability interfaces. It does not duplicate credential, browser, proxy, or
session storage.

The module contains plans, profiles, behaviors, sessions, schedules, limits,
signals, scoring, recommendations, approvals, execution, recovery, analytics,
dashboard, and API packages. The reference execution port validates and
checkpoints resources but deliberately dispatches no live social actions.

## Lifecycle

Plans move through Draft, Pending Approval, Ready, Scheduled, Running, Paused,
Completed, Failed, Cancelled, Archived, and Deleted using an explicit transition
map. There is no unrestricted autonomous mode. Supported modes are Manual
Assisted, Scheduled, Event Triggered, Simulation, Dry Run, and Supervised
Automation.

## Behavior profiles and limits

Profiles allow feed/search browsing, video/profile viewing, and bounded save,
like, follow, comment-draft, and share-draft interfaces. Like, follow, comment
draft, and share draft are treated as high risk and require explicit approval.
Bulk messaging, mass engagement, CAPTCHA bypass, restriction circumvention,
security bypass, and stealth guarantees are outside the module.

Session duration, action/navigation counts, idle intervals, daily/weekly use,
cooldowns, time windows, device references, country references, and proxy
binding references are validated against hard ceilings. Resource limits cover
accounts, workspaces, devices, proxies, sessions, concurrency, navigation
timeouts, and execution timeouts.

## Schedules

Manual, interval, calendar-window, one-time, and recurring schedules include a
timezone, missed-run policy, maximum run count, and optional date boundaries.
Intervals and run counts are bounded.

## Signals, risk scoring, and recommendations

Normalized account, login, session, proxy, browser, restriction, challenge,
rate-limit, and failure-trend signals produce Low, Medium, High, or Critical
risk scores. Scores include factors, reason, action, auto-pause threshold, and
manual-review threshold. A threshold breach pauses matching plans and the
Account Center record through a bounded adapter.

Recommendations suggest schedule, duration, cooldown, action bounds, or pause.
They are always advisory and never mutate or execute a plan.

## Approvals and execution

Approvals record requester, reviewer, notes, expiration, rejection reason, and
the exact behavior scope. High-risk behavior cannot execute without a current
explicit approval.

Execution follows acquire account, acquire browser, acquire proxy, restore
session, validate health, run approved plan, checkpoint, audit, release
resources, and persist outcome. The platform reference implementation performs
validation only; a separately reviewed bounded driver is required to dispatch
any approved activity.

## Recovery and safety

Failed executions can retry only below their maximum attempt count. Browser
recovery, proxy replacement, session restore, checkpoint resume, and manual
intervention are exposed as bounded integration responsibilities. Exponential
backoff belongs to the existing workflow/automation scheduler.

The global kill switch, manual stop, account auto-pause, workspace pause,
approval gates, and risk thresholds take precedence over scheduling. Never put
cookies, sessions, or proxy credentials in metadata or logs. References must
point to encrypted storage.

## Integrations

- Account Center validates ownership and receives auto-pause state.
- Browser Runtime owns browser acquisition, health, restore, and release.
- Proxy Center owns proxy acquisition, health, replacement, and release.
- Workflow and Automation own triggers, retries, backoff, and calendars.
- Existing Audit, RBAC, Metrics, and Observability own cross-platform controls.

All integration ports carry tenant and workspace scope and synchronize only
secret-free references and health state.

## API and dashboard

Collection endpoints are available below `/tiktok/account-farming` for plans,
profiles, schedules, approvals, executions, signals, risks, recommendations,
and analytics. Dashboard and Prometheus metric endpoints are also registered.
Writes are performed through the domain service so callers cannot bypass
validation or approvals.

The dashboard contract covers Plans, Accounts, Profiles, Schedules, Approvals,
Executions, Signals, Risk Scores, Recommendations, Failures, and Statistics.

## Operations guide

1. Confirm tenant/workspace scope and RBAC grants.
2. Confirm referenced accounts exist and encrypted resources are healthy.
3. Create and validate a behavior profile and plan.
4. Request approval; an authorized reviewer decides it before execution.
5. Review risk signals and recommendations.
6. Schedule or manually execute only a Ready plan.
7. Monitor metrics, audit checkpoints, failures, and auto-pauses.
8. Use manual stop, workspace pause, or the kill switch on unsafe state.
9. Resume only after health validation and human review.

### Windows local operations

Use the repository virtual environment from PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_account_farming.py
.\.venv\Scripts\ruff.exe check tiktok\account_farming
.\.venv\Scripts\mypy.exe tiktok\account_farming
```

Tests use bounded doubles and never require live TikTok, browser, or proxy
access. Do not place secrets in environment files, command history, fixtures,
screenshots, or logs.
