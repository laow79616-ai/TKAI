# Hyper Intelligence Operations Guide

Use the health and metrics GET endpoints for readiness and coverage. Diagnostics
report incomplete metadata linkage without mutating a registry. Trace hooks and
structured logs are in-memory metadata projections and should be exported by an
authorized platform observability adapter.

Operational validation includes Ruff, configured mypy, focused and regression
pytest suites, OpenAPI GET-only checks, dashboard and AI Studio production
builds, PowerShell script parsing, and `git diff --check`.

If health degrades, inspect diagnostics and audit records, correct the source
metadata in its owning system, and rebuild the fabric projection. Do not attempt
runtime remediation through this fabric.
