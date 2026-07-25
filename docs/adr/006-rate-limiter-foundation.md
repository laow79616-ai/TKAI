# ADR 006: Rate Limiter Foundation

## Status

Accepted.

## Decision

Use a thread-safe local quota registry, a pluggable strategy interface, and shared Observability EventBus events. Make routing integration an explicit composition strategy rather than changing existing routing policies.

## Rationale

Sliding windows smooth boundary behavior while preserving deterministic offline semantics; fixed windows remain useful where wall-clock policies are desired. The registry separates immutable quota data from strategy-owned transient counters. EventBus reuse avoids a second observability path. Composition preserves Cost and Load strategy compatibility and makes quota filtering opt-in.

## Consequences

This subsystem remains process-local and does not use Redis, distributed synchronization, dynamic quota learning, user-level controls, API Gateway integration, or ProviderManager automatic enforcement.
