# TKAI 8.0.0 General Availability Release Notes

TKAI V8 completes the Hyper Kernel and ten Hyper frameworks. This production-readiness
change adds no business or execution capabilities. V6, V7, TikTok, dashboard, AI
Studio, local-runtime, deployment, configuration, storage, extension, security, and
OpenAPI behavior remain compatible.

Release status: **General Availability (GA)**.

## Frameworks

Exactly 11 completed V8 components are recorded in `FRAMEWORK_MANIFEST_V8.json`.
All V8 HTTP surfaces are read-only advisory, diagnostics, health, or metadata routes.

## Security and observability

The release verifies RBAC; tenant, workspace, and framework isolation; secret
filtering; audit coverage; and runtime governance. V8 exposes no public
execution, mutation, scheduler mutation, workflow start, recovery execution,
snapshot restoration, rollback execution, automatic approval, secret retrieval,
hidden reasoning, or chain-of-thought endpoints.

Metrics, structured logging, tracing hooks, diagnostics, health, audit
correlation, Dashboard projections, and all 11 framework projections are
included in the final verification.

## Upgrade

V8 is additive. Existing V6 and V7 callers require no route or configuration changes.
Review `docs/v8/Upgrade-V7-to-V8.md` before enabling V8 integrations.

## Known issues and prerequisites

Optional external integrations require deployment-owned services and
credentials. Frontend production builds require Node.js 18 or newer and
installed npm dependencies. The Python runtime requires Python 3.10 or newer;
PowerShell 7 is recommended for Windows release validation.
