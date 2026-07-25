# ADR 005: Load-aware Routing Foundation

## Status

Accepted.

## Decision

Collect load passively from the existing Observability EventBus, store immutable snapshots in a thread-safe registry, and provide an opt-in `LoadAwareStrategy` that composes with existing Routing types.

## Rationale

Passive collection avoids additional provider traffic and keeps offline tests deterministic. Reusing EventBus avoids a second event system. Immutable snapshots protect callers from registry mutation. Deterministic scoring makes selection explainable and stable. Cost precedes load so the policy's economics are explicit; load resolves equal-cost choices and excludes saturated options.

## Consequences

`CostAwareStrategy` remains unchanged and applications explicitly choose `LoadAwareStrategy`. Load is process-local and is not distributed, persisted, or learned adaptively. This decision introduces no ProviderManager takeover, rate limiter, retry policy, or cross-region routing.
