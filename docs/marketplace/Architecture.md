# Enterprise Marketplace Architecture

The domain layer in `marketplace.enterprise_store` owns immutable records and a
deterministic in-memory service. Store-specific namespaces re-export narrow
contracts. `marketplace.api` maps the service to JSON-safe HTTP responses;
the dashboard consumes those endpoints; Prometheus composition reads the
service's count-only metrics.

Existing Agent Runtime, Plugin Marketplace, Enterprise Platform, Cloud Native,
AI Studio, Workflow, SDK, Docker, Kubernetes, CI/CD, and observability modules
remain independent. The server application composes the new service using
dependency injection and does not introduce process-wide state.
