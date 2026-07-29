# V7 Unified Event Fabric

## Architecture

The Event Fabric is a synchronous, in-process coordination layer. `EventFabric`
composes immutable contracts, the registry, deterministic router, bounded queue,
delivery, retry, dead-letter, replay, idempotency, metrics, tracing, audit, and
security. It creates no threads, brokers, sockets, browser actions, or external
network dependencies. Publishers enqueue validated envelopes and never invoke
subscribers directly.

## Event Model and Envelope

`EventModel` identifies type and semantic version, source, subject, tenant,
workspace, correlation, causation, trace, timestamp, opaque payload reference,
headers, priority, delivery and retention policies, and safe metadata.
`EventEnvelope` is frozen, versioned, JSON serializable, secret-filtered, size
bounded, and carries a SHA-256 integrity value for its payload reference. Payload
data remains outside the fabric.

## Registry, Publishers, Subscribers, and Subscriptions

The registry indexes versioned event contracts and safe metadata and resolves
publishers, subscribers, handlers, filters, subscriptions, compatibility, and
lifecycle history. Publishers declare allowed event types. Subscribers retain
capability and service references, health, lifecycle, and audit metadata.
Subscriptions bind event types and version ranges to subscribers with filters,
priority, delivery, retry, dead-letter, replay, isolation, and lifecycle state.

## Routing and Dispatch

Routing is deterministic by priority and identifier, version aware, filter aware,
health aware, lifecycle aware, and tenant/workspace isolated. Fallback routes are
considered only when no primary route is eligible. Dispatch is explicitly drained
in bounded batches from a bounded local queue. Pause, shutdown, and kill-switch
state stop draining; no unrestricted worker is created.

## Delivery, Retry, and Dead Letter

Policies are at-most-once, at-least-once simulation, and best effort. Exactly-once
is not claimed. Results record acknowledgement, latency, attempts, failure class,
and audit data. Retry attempts and deterministic backoff tables are bounded.
Exhaustion creates a reviewable dead-letter record referencing the original event.

## Replay, Ordering, and Idempotency

Replay is local, explicit, approval-gated, audited, result-bounded, and
count-bounded. There is no automatic replay. Ordering is limited to none, source,
subject, correlation, or an explicit partition reference; global ordering is not
claimed. Idempotency records a scoped key and fingerprint and reports duplicates.

## Policies and Lifecycle

Contracts cover delivery, retry, dead-letter, replay, retention, security, audit,
and isolation. Event lifecycle values are Registered, Validated, Published,
Routed, Dispatched, Delivered, Acknowledged, Retrying, Dead Lettered, Replayed,
Expired, Rejected, and Archived.

## Security and Safety

The framework remains inside the process boundary. Shared V7 RBAC is reused for
publisher, subscriber, and event-type authorization. Tenant/workspace isolation,
opaque payload references, integrity checking, bounded metadata, recursive secret
filtering, structured audit, pause awareness, governance state, and kill-switch
state are enforced. Cookies, sessions, proxy credentials, account credentials,
and secrets must never be payload references, metadata values exposed in logs, or
audit values. Filters are declarative data only; arbitrary predicates cannot run.

The fabric performs internal coordination only. It cannot perform TikTok,
browser, account, publishing, outreach, CAPTCHA, challenge, anti-detection, spam,
or platform-security actions and cannot bypass runtime restrictions.

## Compatibility and Integration

The implementation uses V7 Foundation contracts and security, retains capability
and service references for Unified Capability Framework and Unified Service Mesh
resolution, and exposes a reference-only V6 adapter. It does not change V6 event,
TikTok, registry, deployment, or dashboard behavior. Existing APIs remain intact.

## Dashboard and API

The dashboard is a read-only projection of overview, registry, publishers,
subscribers, subscriptions, routing, dispatch, delivery, retry, dead letters,
replay, ordering, idempotency, health, metrics, audit, and lifecycle.
`/v7/events/*` routes are GET-only. There is deliberately no public publish route.

## Operations Guide

Check readiness and queue depth before enabling producers. Pause dispatch for
maintenance and drain bounded batches explicitly. Use the kill switch before an
emergency shutdown. Review failed deliveries before approving replay. Replay only
the minimum subscriber/event scope with an approval reference. Monitor all
`v7_event_fabric_*` metrics and audit entries; never log an envelope payload.

## Validation

All tests are mock-only and offline. Run focused Event Fabric tests first, then
V7 foundation, capability, service-mesh, server, deployment, release,
local-runtime, TikTok regression, and full test suites. Run Ruff and configured
mypy, build Dashboard and AI Studio, validate OpenAPI and PowerShell scripts, and
finish with `git diff --check`.
