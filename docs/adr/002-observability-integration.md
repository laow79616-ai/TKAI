# ADR 002: Observability integration

## Status

Accepted.

## Decision

Integrate the observability foundation through read-only `DoctorService` and
`AICommandService` adapters. The EventBus remains independent from metrics,
logging, tracing, providers, and transports. Adapter instances are supplied by
the application rather than created by diagnostic or CLI code.

## Rationale

This keeps diagnostics deterministic and offline, preserves provider lifecycle
ownership, and lets future integrations replace subscribers without changing
the event model. Structured adapters supply useful local inspection now without
coupling TKAI to a specific telemetry vendor.

## Consequences

No V1 public provider, runtime, health, or configuration API changes are
required. Events are retained only in process memory; persistence and remote
export remain outside this sprint.
