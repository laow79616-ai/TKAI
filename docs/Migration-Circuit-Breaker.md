# Circuit Breaker migration note

Circuit Breaker is an optional V1.1 subsystem. Existing V1 public APIs,
providers, runtime, Health, Observability, and configuration behavior remain
unchanged. Applications opt in by constructing a `CircuitBreakerManager` and
passing passive health events to it; no configuration or source migration is
required.
