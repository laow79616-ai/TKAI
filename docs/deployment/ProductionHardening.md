# Production Hardening

## Scope

Marketplace Server V2 adds local production-hardening primitives without
changing Marketplace Foundation contracts, API resource behavior, or Dashboard
routes. Components are per-application objects and are injected into the API
application factory.

## Configuration

`ProductionConfigurationLoader` accepts an explicit `.env` path and/or an
explicit environment mapping. It recognizes only these settings:

- `TKAI_LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, or `ERROR`
- `TKAI_RATE_LIMIT_REQUESTS`
- `TKAI_RATE_LIMIT_WINDOW_SECONDS`
- `TKAI_SECURITY_HEADERS_ENABLED`

Unknown operating-system environment variables are ignored. Unknown entries in
an explicit production `.env` file are rejected, preventing accidental hidden
configuration. Explicit environment mapping values override `.env` values.

## Logging and Metrics

`StructuredLogger` emits JSON through an injected sink and redacts fields whose
names indicate passwords, tokens, secrets, credentials, or authorization data.
`InMemoryMetrics` supplies deterministic local counters only; it has no
Prometheus endpoint, collector, exporter, or background worker.

## HTTP Hardening

The API factory attaches request ID, structured observability, local rate-limit,
exception, and security-header middleware. Security headers are:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- a same-origin baseline Content Security Policy

The default limiter is a thread-safe, fixed-window in-memory implementation.
It can be replaced by dependency injection and is deliberately not a
distributed rate limiter.

## Health and Shutdown

`ProductionRuntime` exposes caller-driven `/health/live`, `/health/ready`, and
`/health/startup` status endpoints in addition to the existing `/health`
Foundation route. Startup and shutdown are registered with the application
lifecycle. Shutdown calls explicitly injected service/storage closers once,
marks the runtime unready, and does not start workers.

## Limitations

- Health signals are lifecycle state, not active dependency probes.
- Metrics, logs, and rate limits are local to one application instance.
- No Kubernetes, service mesh, distributed rate limiting, OpenTelemetry
  Collector, cloud integration, or background worker is included.
