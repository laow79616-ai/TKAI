# TKAI V8 Production Guides

V8 is an additive, read-only advisory layer. It does not start workflows, execute
recovery, mutate runtimes, allocate resources, restore snapshots, expose secrets, or
return hidden reasoning.

## Architecture and frameworks

The Hyper Kernel provides registry, lifecycle, health, diagnostics, configuration,
security scope, events, observability, storage, extensions, and compatibility ports.
Ten Hyper frameworks layer coordination, intelligence, governance, knowledge,
reasoning, decision, planning, simulation, operations, and recovery capabilities on
those contracts. The authoritative inventory is `FRAMEWORK_MANIFEST_V8.json`.

## Compatibility and upgrade

V6 and V7 packages, routes, adapters, dashboard behavior, AI Studio behavior, local
runtime, deployment, configuration, storage, extensions, security, and OpenAPI remain
available. Deploy V8 as an additive upgrade, retain existing environment variables,
run migrations only when separately documented, and validate `/health/live`,
`/health/ready`, and `/openapi.json` before directing traffic.

## Security and observability

Preserve RBAC and tenant/workspace/namespace/framework scope at every boundary.
Metadata is allow-listed and secret values are filtered. Correlate structured logs,
metrics, tracing hooks, diagnostics, health, and audit events with request IDs.
Production operators must respect pause, kill-switch, and maintenance state.

## Deployment and operations

Prerequisites are Python 3.10+, Node.js 18+, and PowerShell 7 (recommended on
Windows). Configure secrets through the deployment secret provider, never `.env` in
an archive. Build both web applications, generate OpenAPI, run the full validation
matrix, build archives, verify checksums, then promote the immutable commit.

## Known issues and troubleshooting

Optional Redis, PostgreSQL, and external integrations require their documented
services. A clean offline core validation does not prove external service
availability. For readiness failures, check configuration validation, dependency
health, request-correlated logs, framework diagnostics, OpenAPI duplicate operation
IDs, and archive checksum results. Do not bypass governance controls to recover a
degraded environment.
