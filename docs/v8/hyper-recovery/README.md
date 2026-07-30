# TKAI V8 Hyper Recovery & Resilience Fabric

## Architecture and recovery model

This package is the local, metadata-driven continuity and restoration-planning
layer spanning V6 AI Centers, V7 frameworks, and V8 fabrics. Frozen contracts
enter typed append-only registries through bounded, allowlisted, read-only
adapters. Projections expose sanitized metadata to the dashboard and GET-only
API. No component owns an executor, runtime client, browser client, scheduler
writer, resource allocator, snapshot restorer, or external network integration.

Lifecycle values describe artifact review state only. `approved-reference`,
`recovering-reference`, and `restored-reference` never authorize or claim
runtime action.

## Incidents, failures, impact, readiness, resilience and continuity

Incidents are immutable references. Failure classifications cover
configuration, dependency, capability, service, workflow, resource, runtime,
storage, delivery, consistency, policy, governance, compatibility, health,
capacity, schedule, and external-reference failures. Root-cause claims require
evidence. Impact and readiness records describe affected boundaries and
preparedness. Resilience redundancy claims require supporting references.
RTO, RPO, and downtime values are advisory metadata.

## Recovery, rollback, snapshots, checkpoints and degraded mode

Recovery steps and plans, rollback plans, restoration plans, snapshot and
checkpoint registrations, and degraded-mode definitions are reference-only.
There are deliberately no execution, restoration, activation, allocation, or
automatic approval endpoints. Payloads remain behind references and hashes.

## Dependencies, resources, capacity and validation

Dependency analysis reports missing and circular references. All source,
incident, step, snapshot, checkpoint, time-horizon, and result collections are
bounded. Resource and capacity records are estimates and never allocate
workers, storage, queues, or recovery windows.

## Evaluations, recommendations, reviews and approvals

Scores contain factors, weights, references, limitations, and a plain-language
summary. Recommendations are handoffs, not commands. Reviews and approvals
apply to artifact quality only and cannot authorize execution.

## Governance, compatibility, versioning and history

Governance references preserve pause, kill-switch, maintenance, risk, security,
review, approval, and audit awareness. Compatibility references support V6,
V7, and V8 without modifying existing APIs or TikTok behavior. New versions
are registered as immutable records with effective-date, supersession,
change-reason, history, and deprecation metadata.

## Analytics, health, metrics and audit

The fabric projects registry totals, quality metrics, diagnostics, health,
internal metadata events, and local audit records. Events use bounded V7 Event
Fabric interfaces and never an external broker or operational responder.

## Security and safety

Reads enforce tenant, workspace, namespace, profile, and RBAC boundaries.
Sensitive keys are redacted; payloads are reference-only. Arbitrary recovery or
validation code, filesystem scanning, network access, secret retrieval, CAPTCHA
or security bypass, publishing, outreach, and direct TikTok/browser/account/
device/proxy actions are excluded.

## Operations guide

Register immutable metadata, validate references, inspect explainable
evaluations, complete human governance review, and hand approved artifacts to
separately governed systems. This fabric stops at the handoff reference.

## Windows local guide

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\v8\hyper_recovery
.\.venv\Scripts\python.exe -m ruff check src\tkai\v8\hyper_recovery tests\v8\hyper_recovery
.\.venv\Scripts\python.exe -m mypy src\tkai\v8\hyper_recovery
```

All tests are offline and mock-only. No TikTok access, accounts, sessions,
proxies, browsers, external recovery service, cloud service, or runtime
mutation is required.
