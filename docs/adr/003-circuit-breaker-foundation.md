# ADR 003: Circuit Breaker Foundation

## Status

Accepted.

## Decision

Use a private state machine with immutable snapshots, a thread-safe registry,
and a replaceable strategy interface. Breakers consume passive Health events
through `CircuitBreakerManager`; they do not query providers or own retry.

## Rationale

The state machine centralizes legal transitions and makes diagnostics stable.
Event-driven integration reuses existing passive health facts without adding
network traffic. The strategy pattern keeps thresholds configurable while
leaving registry and lifecycle behavior deterministic.

## Consequences

This is a foundation only: it does not yet block ProviderManager calls,
implement retry/backoff, route by cost/load, or persist breaker state.
