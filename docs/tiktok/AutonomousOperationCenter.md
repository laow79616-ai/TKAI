# TikTok Autonomous Operation Center

## Architecture

The center is a bounded orchestration layer. It owns missions, plans, approvals,
coordination state, checkpoints, history, monitoring, recovery coordination,
analytics, API contracts, and dashboard projections. It does not own an execution
engine. Dispatch delegates references to the existing Task Scheduler, Automation
Engine, Execution Engine, Workflow Center, and Runtime Manager.

## Mission lifecycle

`Draft -> Planned -> Approved -> Ready -> Running -> Completed -> Archived -> Deleted`

Running missions may pause or recover. Paused and recovering missions may resume.
Active missions may be cancelled. Every transition is checked and audited.

## Execution and monitoring

Only a current approved plan can become ready. Dispatch checks every delegate's
health and TikTok restriction state before coordinating work. Monitoring reports
mission health, progress, resource usage, runtime, queue, risk, and recovery state.
Checkpoints are stored as opaque references; execution remains in existing modules.

## Recovery

Retry, checkpoint resume, rollback, workflow recovery, runtime recovery, and
resource recovery are coordinated through the same injected module ports.
Recovery stops immediately when any module reports an unresolved TikTok
restriction or challenge. CAPTCHA and platform-security bypass are unsupported.

## Security

Every operation requires explicit RBAC permission. Domain objects are tenant and
workspace scoped, cross-scope access is rejected, and approval enforcement is
mandatory. Audit records contain action identifiers only. Metadata rejects secret,
token, cookie, credential, password, and session fields.

## Operations guide

1. Create a bounded mission with objectives, policies, and constraints.
2. Attach a plan containing existing-module task references and rollback data.
3. Obtain a time-bounded approval from an authorized reviewer.
4. Mark the mission ready and dispatch it.
5. Monitor health and checkpoints; pause whenever risk or capacity requires it.
6. Resume or recover only after all TikTok restrictions are resolved.
7. Complete, archive, and retain audit history according to workspace policy.

Metrics are exposed at `/tiktok/autonomous-operation/metrics`; dashboard state is
at `/tiktok/autonomous-operation/dashboard`.

## Windows guide

From PowerShell in the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_autonomous_operation.py
.\.venv\Scripts\python.exe -m ruff check tiktok\autonomous_operation
Set-Location dashboard\frontend
npm run build
```

Tests require no live TikTok access. Production adapters must reuse configured
TikTok services and must not log secrets.
