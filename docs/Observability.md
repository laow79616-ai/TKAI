# Observability

TKAI's observability foundation is an in-memory, framework-neutral event layer.
It does not export telemetry or issue network requests.

## Event model

All runtime events inherit from immutable `Event`. Every event includes a UTC
timestamp and may include a `trace_id` and `correlation_id`. Standard event
types are `RequestStarted`, `RequestCompleted`, `ProviderSelected`,
`ProviderFailed`, `FallbackTriggered`, `HealthChanged`, `ConfigurationLoaded`,
and `CredentialLoaded`.

An `EventBus` retains events in publication order and invokes subscribed
handlers. `EventDispatcher` fans an event out to `Subscriber` implementations.
Subscribers decide whether they support an event before handling it.

## Adapters

`MetricsAdapter`, `LoggerAdapter`, and `TraceAdapter` are in-memory reference
subscribers. They collect counters, structured JSON records, and trace spans
respectively. They deliberately have no Prometheus, OpenTelemetry, or network
export dependency.

## Diagnostics and CLI

`DoctorService` only reads observability objects. It reports EventBus,
dispatcher, subscriber count, and configured adapter availability. The command
below exposes the same safe summary; it never prints event payloads or secrets.

```console
tkai ai observability
tkai ai observability --json
```

`recent_events` contains event metadata only: name, timestamp, trace ID, and
correlation ID. Event data remains inside the owning process.
