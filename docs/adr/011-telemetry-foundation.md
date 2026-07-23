# ADR 011: Telemetry Foundation

## Decision

Use a unified exporter protocol with a thread-safe, inert `LocalExporter` as
the default. Keep correlation context independent of exporters and use explicit
Runtime and Policy Engine adapters.

## Rationale

The explicit adapters preserve existing Runtime, ProviderManager, and AIClient
defaults. Typed local models permit deterministic offline tests and make future
exporters possible without coupling the foundation to a particular telemetry
SDK or network protocol. Exporter errors are isolated because telemetry must
not interrupt primary framework work.

## Consequences

The foundation is intentionally process-local and must be explicitly started.
Future OTLP or vendor exporters can implement the protocol without changing the
public Runtime API.
