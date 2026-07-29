# V7 Unified Data & Storage Framework

## Architecture and data contracts

The framework is a local, metadata-only control plane under
`tkai.v7.data_framework`. Immutable contracts describe models, reference-only
records, declarative schemas, repositories, adapters, queries, filters, sorting,
pagination, index plans, transaction simulations, snapshots, semantic versions,
retention policies, archive plans, and migration assessments.

The in-memory registry is bounded to 1,000 entries per category. Every item is
tenant, workspace, and namespace scoped. Registration validates cross-references
within the same scope. Sensitive payloads and snapshots are represented only by
references and SHA-256 metadata. Declarative schemas contain no executable
validators; query fields must be schema allowlisted.

## Storage, repositories, and compatibility

Supported adapter metadata kinds are memory, local file, SQLite metadata,
existing repository, V6 database compatibility, snapshot, test, and mock.
Adapters expose metadata only: availability, readiness, connection references,
health, diagnostics, and compatibility. They never open network connections or
create production databases. Repository contracts expose bounded read metadata;
mutation is internal and no public mutation route exists.

Compatibility projections advertise the V6 boundary and the V7 foundation,
capability, service mesh, event fabric, state, workflow, resource, security,
observability, configuration, extension, and AI integration points. Existing V6
storage, APIs, deployments, TikTok behavior, and dashboards are unchanged.

## Queries, indexing, snapshots, integrity, and validation

Queries cap results at 1,000, pages at 100, sort fields at five, time ranges at
366 days, and timeout metadata at 30 seconds. Raw SQL and arbitrary expressions
are not contracts. Indexes are plans only. Transactions are local simulations
and never claim distributed semantics. Snapshot payloads are bounded and
reference-only. Hash, schema, reference, version, repository, compatibility,
index, and audit-chain integrity are metadata checks.

## Retention, archival, migration, security, and safety

Retention supports active, historical, audit, snapshot, archived, and temporary
test policy metadata. Purging is never automatic. Archive plans and migration
assessments are immutable advisory artifacts with approval, integrity, rollback,
risk, and audit references; neither is executable.

The framework rejects secret-shaped safe metadata, redacts secret fields during
serialization, isolates scopes, allows local paths/references only, and has no
network, raw SQL, filesystem scan, browser, TikTok, account, publishing,
scheduler, allocation, deletion, migration, schema mutation, or production-index
operation. Host governance, pause, kill-switch, security, RBAC, and audit systems
remain authoritative.

## Operations and Windows local guide

All public endpoints are GET-only at `/v7/data/<projection>` and require
`tenant`, `workspace`, and optionally `namespace`. Use the health, metrics,
audit, integrity, validation, and compatibility projections for operations.

On Windows PowerShell, activate `.venv`, then run:

```powershell
python -m pytest tests/v7/data_framework
python -m ruff check src/tkai/v7/data_framework tests/v7/data_framework
python -m mypy src/tkai
```

No external service, cloud database, browser, real account, cookie, session,
proxy, or network access is needed.
