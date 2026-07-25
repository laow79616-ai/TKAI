# Rate Limiter Foundation

TKAI Rate Limiter is an optional, process-local quota subsystem. It does not contact providers, use Redis, synchronize nodes, or automatically take over `ProviderManager`.

## Quota model and registry

`RateLimitSnapshot` is immutable and contains provider, scope, requests-per-second, requests-per-minute, tokens-per-minute, observed consumption, remaining capacity, and UTC reset/update timestamps. `QuotaRegistry` is thread-safe and returns stable immutable snapshots.

## Strategies

`SlidingWindowStrategy` is the default. It uses bounded timestamp deques to enforce rolling one-second and one-minute request limits plus one-minute token limits. `FixedWindowStrategy` provides deterministic wall-clock windows. `TokenBucketStrategy` is an abstract extension interface; no token-bucket algorithm is enabled in this release.

## Routing integration

`RateLimitAwareStrategy` is an explicit composition around an existing `RoutingStrategy`. It performs a non-consuming quota check and excludes only registered providers whose local quota rejects another request. Existing `CostAwareStrategy` and `LoadAwareStrategy` behavior is unchanged unless an application explicitly wraps them.

## Events and observability

`QuotaConsumed`, `RateLimitExceeded`, and `QuotaReset` inherit from the shared Observability event model and are published through an injected existing `EventBus`. Existing Metrics, Logger, and Trace subscribers can observe the quota decision events without an exporter dependency.

## Doctor and CLI

```console
tkai ai rate-limit
tkai ai rate-limit --json
```

The command displays provider, scope, configured limits, remaining requests/tokens, and reset timestamp. Doctor reports registry size, strategy, exhausted quota state, EventBus availability, and optional routing composition.

## Known limitations

All state is local process memory. There is no distributed synchronization, user-level quota, dynamic learning, API Gateway integration, retry integration, or ProviderManager default takeover.
