# Marketplace Server Health Foundation

## Purpose

`server.health` provides a **Reference Only**, **Offline Only**, **Pure
Memory** Health domain. It stores caller-provided Health checks and results;
it does not execute any check. This concrete Foundation preserves the original
passive `HealthCheck`, `HealthReport`, and `HealthSnapshot` compatibility
contracts while adding explicit lifecycle, event, statistics, and storage
contracts.

## Boundary

```
ReferenceHealthService
        ↓
  HealthStorage protocol
        ↓
ReferenceHealthStorage
```

The domain is independent of Registry, Publisher, Package, Version, Search,
and Statistics. A caller registers every `HealthCheck` and supplies every
`HealthResult` explicitly. No service is discovered or accessed implicitly.

## Models

Immutable JSON-safe models include `HealthCheckId`, `HealthCheck`,
`HealthResult`, `HealthSnapshot`, `HealthStatistics`, `HealthEvent`,
`HealthEventType`, `HealthStatus`, and `HealthSeverity`. Metadata is
defensively copied and deterministically ordered.

Current Health statuses are healthy, degraded, unhealthy, and unknown.
Severities are info, warning, and critical. Legacy passive report values pass,
warning, and error remain available solely for compatibility with the original
Server architecture contract.

## Storage, service, and lifecycle

`HealthStorage` supports check registration/removal, caller-driven result
updates, check retrieval/listing, snapshots, fresh statistics, events, clear,
and close. `ReferenceHealthStorage` is thread-safe, per instance, deterministic
and in-memory only.

Duplicate check identifiers are rejected. Results require a registered check.
Removing a check removes its current result. Clear removes checks and results
but preserves event history. Close is idempotent; final snapshots, statistics,
and events remain readable while new registrations, updates, removals, and
normal check reads fail with `HealthClosedError`.

## Events, statistics, and snapshots

Events use a monotonic sequence, never timestamps. They describe check
registration, removal, result updates, clear, and close. `HealthStatistics`
derives total checks and healthy, degraded, unhealthy, and unknown current
counts from the explicit in-memory state. `HealthSnapshot` contains stable
ordered checks, results, events, statistics, the legacy passive report, and
closed state.

## Explicit non-goals

There is no HTTP endpoint, FastAPI, GraphQL, Kubernetes liveness/readiness
probe, Prometheus exporter, OpenTelemetry integration, automatic monitoring or
polling, scheduler, background worker, network/database/filesystem check,
remote monitoring, authentication, authorization, database, Redis, or global
state. This module does not perform health probes of any kind.
