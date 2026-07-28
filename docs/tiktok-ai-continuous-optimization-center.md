# TikTok AI Continuous Optimization Center

## Architecture

The center is a single-user local advisory control plane. Read-only adapters collect
bounded snapshots from existing TikTok modules. The domain service creates versioned
baselines, explainable candidates, offline experiments, evaluations and recommendations.
It never uses live TikTok access. Approved changes are delegated to existing
configuration, execution, scheduler, runtime, resource, workflow, automation, recovery,
backup, checkpoint and rollback interfaces.

## Lifecycle and operations

Profiles move through Draft, Collecting, Analyzing, Proposed, Pending Review, Approved,
Applying, Validating, Completed, Rejected, Rolled Back, Failed, Archived and Deleted.
Operators capture a baseline, add evidence-backed signals, run dry-run/simulation/shadow
or historical replay experiments, evaluate confidence and risk, and submit advisory
recommendations. Canary and A/B contracts remain interfaces and require approval.

Every application requires an unexpired human approval, the expected configuration
version, a valid backup, a valid checkpoint and a bounded candidate. Post-change health,
performance, resources, failures, recovery and risk are evaluated during the observation
window. A regression delegates rollback to the existing rollback interface.

## Scope, objectives and safety

Supported scopes are runtime, browsers, devices, proxies, scheduler, resources,
workflows, automation, execution, recovery, publishing, collection, interaction, risk,
analytics and local runtime. Objectives include reliability, availability, latency,
throughput, queues, recovery, lifecycle time, resource consumption and utilization.
Custom objectives must remain bounded.

Safe defaults cap a candidate at 20%, with an absolute maximum of 25%. Human approval,
rollback, workspace/account pause, kill-switch, restriction/challenge awareness and risk
policy checks belong in the delegated precondition interface. CAPTCHA bypass,
restriction circumvention, security bypass, anti-detection guarantees, spam and
unrestricted mass actions are prohibited. Metadata and audit records reject secrets.
Analysis adapters are read-only and all records enforce tenant/workspace isolation and
RBAC.

## Integrations, history and analytics

Adapters cover the Decision Center, Control Tower, Recovery Center, Execution Engine,
Operations Planner, Automation Engine, Runtime Manager, Resource Center, Scheduler,
Browser Cluster, Device and Account Centers, Browser Runtime, Proxy and Workflow
Centers, Operations, Risk, Content, Publishing, Collection, Interaction, Analytics and
Local Runtime. Evidence, audit, events, metrics, observability, security, approval,
backup and checkpoint infrastructure is reused rather than duplicated.

History includes profile versions, baselines, candidates, experiments, recommendations,
approvals, changes, validations, rollbacks and audit. Analytics reports generated and
approved recommendations, applied/rejected changes, rollbacks, success/regression rates,
improvements, duration and resource references.

## Windows local guide

Run all commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\tiktok\test_optimization_center.py
.\.venv\Scripts\python.exe -m ruff check tiktok\optimization_center tests\tiktok\test_optimization_center.py
.\.venv\Scripts\python.exe -m mypy tiktok\optimization_center
```

The HTTP surface is rooted at `/tiktok/optimization-center`. Metrics and dashboard
endpoints expose local state only. Production adapters must use existing bounded
interfaces and must never store cookies, sessions, proxy credentials or secrets.
