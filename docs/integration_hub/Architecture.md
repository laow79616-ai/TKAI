# Enterprise AI Integration Hub Architecture

The hub is a tenant- and workspace-scoped control plane layered on the existing
integration, event streaming, API management, automation, operations, security,
model, data, governance, collaboration, reasoning, memory, and orchestration
platforms. Connector adapters own external I/O; the hub owns catalog metadata,
instances, declarative mappings, flows, policies, schedules, health, analytics,
audit records, retries, and dead letters. Docker, Kubernetes, CI/CD, and
observability use the existing TKAI deployment foundations.
