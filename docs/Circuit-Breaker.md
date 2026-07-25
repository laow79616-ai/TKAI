# Circuit Breaker

TKAI provides an in-memory circuit breaker foundation that is independent of
providers, transports, retry policy, and routing. It records passive outcomes
and does not perform health probes or network calls.

## State machine

Each provider has one `CircuitBreaker` whose state is private and exposed as an
immutable `CircuitBreakerSnapshot`:

```text
CLOSED -- consecutive failures --> OPEN -- open duration --> HALF_OPEN
HALF_OPEN -- probe successes --> CLOSED
HALF_OPEN -- one failure --> OPEN
```

`ThresholdStrategy` defaults to five consecutive failures, a 30-second open
duration, and three half-open successes. Applications may supply another
`CircuitBreakerStrategy` without changing registry or manager behavior.

## Registry and health events

`CircuitBreakerRegistry` is thread-safe and stores a single breaker per
provider. `CircuitBreakerManager.handle_health_event()` consumes passive
`HealthEvent` values: unhealthy events open the breaker, degraded events record
a failure, recovered events record a success, and reset events reset it. The
caller owns event delivery; the breaker never probes providers.

## Diagnostics and CLI

`DoctorService` reports registry size, strategy, and provider states without
mutating breaker state. The CLI produces the same safe snapshot data:

```console
tkai ai breaker
tkai ai breaker --json
```

Output includes provider, state, failure count, success count, and consecutive
failures. It contains no configuration values or credentials.
