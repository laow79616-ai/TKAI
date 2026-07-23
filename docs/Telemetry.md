# Telemetry Foundation

`tkai.telemetry` is an optional, process-local telemetry foundation. It offers
typed metrics, spans, correlation context, and structured logs without adding a
network exporter or changing existing provider execution.

## Architecture

`TelemetryManager` coordinates a thread-safe `TelemetryRegistry`, local metric
and trace registries, and the structured logging adapter. `LocalExporter` is
registered by default but remains inert until `TelemetryManager.start()` is
called. Exporter failures are isolated from local collection.

The exporter protocol has synchronous and asynchronous start, stop, metric,
trace, and log operations. This keeps future exporters interchangeable without
making them a dependency of Runtime or ProviderManager.

## Metrics, traces, and context

`Metric` supports counter, gauge, and histogram kinds. `TraceRegistry` creates
and completes immutable `TraceContext` values. `CorrelationContext` is
immutable, copyable, inheritable, and JSON-ready, so callers can safely carry
request, correlation, and trace identifiers across their own boundaries.

`TelemetryLoggingAdapter` creates structured records and redacts common secret
field names, including nested `api_key`, `authorization`, `token`, `password`,
and `secret` values before records are retained or exported.

## Explicit integrations

`TelemetryRuntimeAdapter` and `TelemetryPolicyAdapter` are opt-in adapters.
They do not modify Runtime, ProviderManager, or AIClient defaults. Lifecycle
and data events are published to an injected `EventBus`. `DoctorService` can
report local telemetry status, while `tkai ai telemetry [--json]` displays a
read-only summary.

## Known limitations

No OpenTelemetry, Prometheus, Jaeger, Zipkin, OTLP, HTTP, gRPC, or other network
exporter is included. All state is local, in memory, and intentionally not
durable or distributed.
