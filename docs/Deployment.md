# Cloud Deployment Foundation

Cloud Deployment is a reference-only declaration layer. It provides immutable
deployment descriptors, explicit context, target and strategy descriptions,
deterministic plans, lifecycle transition validation, result descriptors, and
an in-memory reference service. It never calls Kubernetes, Docker, a cloud API,
Shell, network, database, storage backend, or execution engine.

Targets may describe local, container, Kubernetes, serverless, VM, managed, or
external destinations; these kinds never open a connection. Plans validate
duplicate IDs, unknown dependencies, and simple self cycles only. The reference
service stores descriptors locally, supports explicit transitions and idempotent
close, and performs no provisioning, rollback, audit, or license operation.
# TKAI V6.0 Deployment Guide

V6.0 supports the existing Docker Compose, Kubernetes/Helm, and local Windows
profiles. Build both web clients before packaging:

```powershell
npm --prefix dashboard/frontend ci
npm --prefix dashboard/frontend run build
npm --prefix studio/frontend ci
npm --prefix studio/frontend run build
```

Use environment-backed secret references; never place credentials in
configuration files or images. Validate the production environment with
`python scripts/check_ga_environment.py`, generate the package with
`scripts/build-release.ps1`, and validate it with
`scripts/validate-release.ps1`.

Before accepting traffic, confirm `/health`, `/metrics`, and `/openapi.json`,
database initialization, startup/shutdown, backup/restore, diagnostics, TLS,
RBAC assignments, tenant/workspace boundaries, and log redaction. Keep the
existing execution adapters disabled unless explicitly configured under the
approved deployment architecture.
