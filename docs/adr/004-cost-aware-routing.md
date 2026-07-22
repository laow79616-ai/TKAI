# ADR 004: Cost-aware Routing Foundation

## Status

Accepted.

## Decision

Adopt a strategy pattern operating on immutable provider metadata and a separate immutable decision model. The router reads existing Health and Circuit Breaker registries rather than creating probes or changing provider behavior.

## Rationale

Strategies let future load-aware or adaptive policies be added without duplicating registry logic. Metadata separates static provider economics from runtime health. The decision model makes each choice explainable to Doctor, CLI, and future observers without exposing credentials.

## Consequences

The initial strategy is intentionally conservative: only HEALTHY providers are eligible, OPEN breakers are excluded, and HALF_OPEN candidates are penalized. No retry, cost learning, load balancing, or ProviderManager integration is introduced by this foundation.
