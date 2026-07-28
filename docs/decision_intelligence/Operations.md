# Operations

Expose `DecisionMetrics.render_prometheus()` through the existing observability
endpoint. Alert on elevated decision latency, falling execution success, stalled
approvals, and evaluation or recommendation volume anomalies.

The control plane is stateless apart from its reference in-memory repositories.
Production deployments should provide durable tenant-scoped repositories,
backups, retention controls, health checks, horizontal scaling, and event
delivery through existing Docker, Kubernetes, CI/CD, and observability
facilities. Release validation must run lint, type checking, the complete test
suite, deployment checks, release checks, frontend builds, and whitespace
validation.
