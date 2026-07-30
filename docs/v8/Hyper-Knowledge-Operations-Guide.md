# Hyper Knowledge Operations Guide

Use `/v8/knowledge/health` for readiness and diagnostics and
`/v8/knowledge/metrics` for registry and audit counters. Structured logs, trace
correlation hooks, diagnostics, and audit records are exposed through local
fabric snapshots. All public HTTP knowledge routes use GET.

Validate changes with Ruff, configured mypy, focused and regression pytest
suites, frontend production builds, OpenAPI inspection, PowerShell parsing, and
`git diff --check`. No validation requires live TikTok access.
