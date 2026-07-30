# Operations Guide

Monitor `/v9/governance/health` and `/v9/governance/metrics`, and inspect the
dashboard audit and diagnostics projections. All governance endpoints are
GET-only. Treat unhealthy dependencies as metadata-source issues; the mesh
must not attempt remediation or runtime mutation.

Validate with Ruff, configured mypy, pytest, frontend production builds,
OpenAPI inspection, PowerShell parser checks under `scripts/`, and
`git diff --check`.
