# Cost-aware Routing

TKAI's Routing Foundation is a provider-neutral, passive decision layer. It does not call providers, change `ProviderManager`, probe Health, or mutate Circuit Breakers.

## Flow

`RoutingManager` owns immutable `ProviderMetadata` in a thread-safe `RoutingRegistry`. `ProviderRouter` joins metadata with passive `HealthRegistry` and `CircuitBreakerRegistry` snapshots, then delegates to a pluggable `RoutingStrategy`.

The default `CostAwareStrategy` deterministically excludes OPEN breakers, excludes non-HEALTHY providers, checks required capabilities, orders by total prompt-plus-completion cost per 1K tokens, then breaks ties by priority, weight, and provider name. HALF_OPEN breakers are eligible but penalized behind CLOSED breakers at the same cost.

Every attempt returns an immutable `RoutingDecision` with candidate names, reason, cost, priority, weight, Health status, Breaker state, and timestamp.

## Metadata

`ProviderMetadata` contains provider name, priority, weight, prompt and completion costs, declared capabilities, and optional tags. It is immutable, so changing routing assumptions means registering new metadata explicitly.

## Diagnostics and CLI

Doctor reports registry size, strategy, metadata, and whether passive Health and Breaker registries are connected. It performs no provider calls.

```console
tkai ai routing
tkai ai routing --json
```

The command prints registered providers, strategy name, safe metadata, and a simulated decision based only on current in-memory snapshots.
