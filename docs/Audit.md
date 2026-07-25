# TKAI Enterprise Audit Foundation

## Architecture

Audit Foundation provides explicit, immutable event contracts and a bounded,
in-memory `ReferenceAuditService` for tests and development. Nothing registers a
global logger or automatically observes Runtime, SDK, Studio, or REST actions.

## Context, Actors, Targets, and Outcomes

`AuditContext` carries caller-supplied tenant, organization, workspace, user,
principal, request, correlation, trace, and span identifiers. Actors, targets,
and outcomes are immutable descriptors. They carry no credentials, token,
authorization header, ORM object, or stack trace by default.

## Events and Queries

`AuditEvent` has a UTC timestamp, schema version, stable JSON-safe snapshot,
actor, target, outcome, and explicit context. `AuditQuery` describes filtering,
stable ordering, offset/limit paging, and an optional next cursor. It is not a
SQL query and does not perform full-text search.

## Redaction, Retention, and Integrity

Redaction supports bounded recursive remove/mask, metadata handling, allow and
deny lists, and string truncation. Default sensitive-name matching includes
password, secret, token, authorization, api_key, credential, private_key, and
cookie. It returns a new representation without changing the source event.

Retention and legal-hold descriptors are declarations only: no archive,
deletion, enforcement, or compliance certification occurs. The SHA-256 reference
integrity verifier hashes explicit event serialization only; it provides no
signature, key management, or tamper-proof storage guarantee.

## Reference Service and Mapping Boundaries

`ReferenceAuditService` is thread-safe, deterministic, bounded, and explicitly
owned. Capacity is configured to reject or evict the oldest event. It uses no
network, disk, environment, exporter, database, Redis, Kafka, SIEM, or
OpenTelemetry integration. Mapping helpers convert existing Enterprise
descriptors to audit descriptors as pure functions and never record an event.

## Compliance Disclaimer and Limitations

This foundation is not a compliance certification, audit exporter, immutable
ledger, or security-monitoring system. It has no persistence, SIEM/exporter,
real tamper-proof store, signatures, key management, or automatic interception.
ReferenceAuditService is for tests and development only.
