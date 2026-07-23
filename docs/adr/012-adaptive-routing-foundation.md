# ADR 012: Adaptive Routing Foundation

## Decision

Use deterministic rules over bounded, local provider history. Normalize explicit
weights, retain a confidence score, use neutral cold-start scores, and break ties
by provider name. Integrate only through explicit Runtime and Policy adapters.

## Rationale

Rules are transparent and testable without model training or external services.
Bounded history prevents unbounded memory use, while confidence distinguishes a
new provider from a well-observed one. An open breaker is a hard exclusion, and
stable ordering avoids accidental traffic shifts.

## Consequences

Adaptive routing remains an additive opt-in feature. It neither replaces the
existing router nor changes ProviderManager defaults. Local state is not shared
across processes and deliberately does not claim global provider load.
