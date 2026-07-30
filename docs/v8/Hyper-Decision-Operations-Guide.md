# Hyper Decision Operations Guide

The fabric is in-memory and advisory. Monitor `health`, `metrics`, diagnostics,
structured logs, traces, and audit projections. All public decision endpoints are
GET-only. A healthy response explicitly reports execution, runtime mutation, and
automatic approval as disabled.

Validate with Ruff, configured mypy, mock-only Hyper Decision tests, V8/V7/full
pytest suites, regression/deployment/release/local-runtime tests, frontend production
builds, OpenAPI inspection, PowerShell parsing under `scripts/`, and
`git diff --check`.
