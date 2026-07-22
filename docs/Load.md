# Provider Load Subsystem

TKAI Load is a passive, single-process in-memory subsystem. It describes the work observed by this TKAI process only; it is not a provider's global service load and does not make network probes.

## Passive collection

`PassiveLoadCollector` subscribes to the existing Observability `EventBus`. `RequestStarted`, `RequestCompleted`, and `ProviderFailed` events carrying a provider name update immutable `ProviderLoadSnapshot` values. Active requests are clamped at zero, so duplicate or out-of-order completion/failure events do not corrupt counters.

Latency is retained in a bounded in-memory deque. Average, P95, and P99 use a deterministic nearest-rank percentile calculation; empty samples report zero.

## Evaluation and events

`LoadEvaluator` classifies snapshots as UNKNOWN, LOW, NORMAL, HIGH, or SATURATED using configurable utilization, pending-work, latency, and error-rate thresholds. A status transition publishes an immutable `LoadChanged`, `ProviderLoadHigh`, `ProviderSaturated`, or `ProviderLoadRecovered` event to the shared EventBus. No event is emitted when the status is unchanged.

## Load-aware routing

`LoadAwareStrategy` is opt-in and leaves `CostAwareStrategy` unchanged. It preserves CostAware capability, Health, and OPEN-breaker filtering, excludes SATURATED providers, and keeps UNKNOWN snapshots behind known LOW/NORMAL candidates. Its deterministic order is cost first, then load score, then HALF_OPEN penalty, priority, weight, and provider name.

## CLI and Doctor

```console
tkai ai load
tkai ai load --json
```

The CLI reports stable local snapshot fields. Doctor reports registry count, collector/evaluator wiring, EventBus subscription, routing-strategy integration, and HIGH/SATURATED providers. No output includes credentials or provider responses.

## Known limitations

Snapshots are neither persisted nor synchronized across processes or regions. There is no active probing, automatic scaling, rate limiting, retry policy, or ProviderManager default takeover.
