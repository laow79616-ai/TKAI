# V8 Governance Operations Guide

## Read endpoints

- `GET /v8/governance/profiles`
- `GET /v8/governance/policies`
- `GET /v8/governance/constraints`
- `GET /v8/governance/compliance`
- `GET /v8/governance/reviews`
- `GET /v8/governance/approvals`
- `GET /v8/governance/compatibility`
- `GET /v8/governance/health`
- `GET /v8/governance/metrics`

There are no mutation endpoints. Health reports source counts, diagnostics, and
the disabled execution, mutation, and automatic-approval boundaries. Metrics
report registry and aggregation counts. Audit, structured logs, and tracing
hooks are available through the in-process snapshot and dashboard projection.

Operators should investigate pending reviews and policies without framework
references. These diagnostics are advisory and do not block runtime.
