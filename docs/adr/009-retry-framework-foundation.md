# ADR 009: Retry Framework Foundation

## Decision

Introduce `tkai.retry` as an explicit, provider-neutral retry service with
immutable per-operation budgets, deterministic pluggable backoff strategies,
and EventBus observability.

## Rationale

Retry behavior needs to be reusable by future explicit call paths without
changing the stable ProviderManager, Runtime, or AIClient defaults.  A local
manager and injected sleeper keep tests offline and deterministic.  Classifying
only transient, timeout, and rate-limit-shaped failures as retryable avoids
silently repeating invalid requests.

## Consequences

Applications opt in by calling `RetryManager` or registering
`RetryPolicyAdapter` in an explicit Policy Engine.  This decision deliberately
does not add distributed state, Redis, hedged requests, or automatic provider
integration.
