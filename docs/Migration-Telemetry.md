# Telemetry migration note

Telemetry is additive. Existing Runtime, ProviderManager, and AIClient callers
need no change, and no default execution path begins exporting telemetry.

To use process-local telemetry, create a `TelemetryManager` and explicitly call
`start()` before exporting records. Runtime and Policy Engine integration remain
explicit through their corresponding adapters. No V1.1 configuration or public
API migration is required.
