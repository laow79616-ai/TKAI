# Reliability

Connector execution uses bounded attempts, timeout configuration, idempotency,
deduplication, failure metrics, correlation IDs, and tenant-scoped dead letters.
Backoff and circuit breakers are adapter interfaces so production runtimes can
use their native non-blocking implementations.
