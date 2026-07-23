# Adaptive Routing Foundation

`tkai.adaptive` provides an optional, deterministic provider-ranking layer. It
does not replace `RoutingManager`, `ProviderManager`, Runtime, or AIClient.
Callers explicitly create an `AdaptiveRoutingManager` and call `select_provider`
or install an explicit Runtime or Policy adapter.

## Architecture

`ProviderHistory` retains a bounded, thread-safe local history of safe
`ProviderSignal` values. `AdaptiveScoringEngine` converts its aggregate
statistics into normalized component scores. `AdaptiveRouter` filters and ranks
only the candidates supplied by the caller, with provider-name tie breaking.

## Signals, scoring, and confidence

Signals contain latency, outcome, cost, load, availability, breaker, rate-limit,
and retry information; they never contain request or response bodies. The
default normalized weights are reliability 0.35, latency 0.25, health 0.20,
cost 0.10, and load 0.10. Confidence rises from zero to one as the configured
minimum sample count is reached.

At cold start, a provider receives neutral component scores and low confidence;
it remains selectable. An open breaker or unavailable provider is always
ineligible. Rate limiting lowers health score rather than silently selecting a
different legacy route.

## Integration and observability

`AdaptiveRoutingRuntimeAdapter` records each real attempt once and skips cache
hits. `AdaptiveRoutingPolicyAdapter` is opt-in and only writes its decision to
`PolicyContext`; it does not override an explicit provider unless configured.
The manager emits immutable events through an injected EventBus and isolates
subscriber exceptions. `DoctorService` and `tkai ai adaptive-routing --json`
display local state without invoking providers.

## Offline example

```python
from datetime import datetime, timezone
from tkai.adaptive import AdaptiveRoutingManager, ProviderSignal

manager = AdaptiveRoutingManager()
manager.record_signal(ProviderSignal("primary", datetime.now(timezone.utc)))
decision = manager.select_provider(["primary", "backup"])
assert decision.selected_provider == "primary"
```

## Known limitations

History is bounded and process-local. There is no machine learning, distributed
aggregation, Redis history, active health probing, multi-region routing, or
automatic traffic migration. Existing routing remains the default.
